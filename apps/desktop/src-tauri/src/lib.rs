use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use serde::Serialize;
use sysinfo::System;
use tauri::{AppHandle, Manager, RunEvent};
use tauri_plugin_deep_link::DeepLinkExt;

#[cfg(target_os = "windows")]
use std::os::windows::io::AsRawHandle;
#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

// ---------------------------------------------------------------------------
// Windows Job Object — ensures ALL descendant processes are killed when the
// handle is dropped, regardless of parent-child relationships.
// ---------------------------------------------------------------------------

#[cfg(target_os = "windows")]
mod winjob {
    use std::ffi::c_void;
    use std::ptr;

    // Win32 constants
    const JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: u32 = 0x00002000;
    const JOB_OBJECT_EXTENDED_LIMIT_INFORMATION: u32 = 9;

    #[repr(C)]
    #[derive(Clone, Copy)]
    struct IoCounters {
        read_operation_count: u64,
        write_operation_count: u64,
        other_operation_count: u64,
        read_transfer_count: u64,
        write_transfer_count: u64,
        other_transfer_count: u64,
    }

    #[repr(C)]
    #[derive(Clone, Copy)]
    struct JobObjectBasicLimitInformation {
        per_process_user_time_limit: i64,
        per_job_user_time_limit: i64,
        limit_flags: u32,
        minimum_working_set_size: usize,
        maximum_working_set_size: usize,
        active_process_limit: u32,
        // ULONG_PTR on Windows — 4 bytes on 32-bit, 8 bytes on 64-bit
        affiliate_process_limit: usize,
        priority_class: u32,
        scheduling_class: u32,
    }

    #[repr(C)]
    #[derive(Clone, Copy)]
    struct JobObjectExtendedLimitInformation {
        basic_limit_information: JobObjectBasicLimitInformation,
        io_info: IoCounters,
        process_memory_limit: usize,
        job_memory_limit: usize,
        peak_process_memory_used: usize,
        peak_job_memory_used: usize,
    }

    // SAFETY: These are plain-data repr(C) structs with no pointers or Drop.
    unsafe impl Send for JobObjectExtendedLimitInformation {}

    extern "system" {
        fn CreateJobObjectW(lpjobattributes: *const c_void, lpname: *const u16) -> *mut c_void;
        fn AssignProcessToJobObject(hjob: *mut c_void, hprocess: *mut c_void) -> i32;
        fn SetInformationJobObject(
            hjob: *mut c_void,
            jobobjectinfoclass: u32,
            lpjobobjectinfo: *const c_void,
            cbjobobjectinfolength: u32,
        ) -> i32;
        fn CloseHandle(hObject: *mut c_void) -> i32;
    }

    /// RAII wrapper around a Windows Job Object handle.
    ///
    /// When dropped, the handle is closed. If `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`
    /// was set, all processes assigned to the job are terminated immediately by the
    /// kernel — this is deterministic and race-free.
    pub struct JobHandle(*mut c_void);

    // SAFETY: Job handle is thread-safe (kernel object).
    unsafe impl Send for JobHandle {}

    impl JobHandle {
        /// Create a new Job Object. Returns `None` on API failure.
        pub fn create() -> Option<Self> {
            unsafe {
                let h = CreateJobObjectW(ptr::null(), ptr::null());
                if h.is_null() {
                    return None;
                }
                Some(JobHandle(h))
            }
        }

        /// Configure the job to kill all processes when the last handle is closed.
        pub fn set_kill_on_close(&self) -> bool {
            unsafe {
                let mut info: JobObjectExtendedLimitInformation = std::mem::zeroed();
                info.basic_limit_information.limit_flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                SetInformationJobObject(
                    self.0,
                    JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                    &info as *const _ as *const c_void,
                    std::mem::size_of::<JobObjectExtendedLimitInformation>() as u32,
                ) != 0
            }
        }

        /// Assign a process (by raw HANDLE) to this job. Returns true on success.
        pub fn assign_process(&self, process_handle: *mut c_void) -> bool {
            unsafe { AssignProcessToJobObject(self.0, process_handle) != 0 }
        }
    }

    impl Drop for JobHandle {
        fn drop(&mut self) {
            unsafe {
                CloseHandle(self.0);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Startup status (unchanged)
// ---------------------------------------------------------------------------

#[derive(Clone, Serialize)]
pub struct StartupStatus {
    pub stage: String,
    pub message: String,
    pub error: Option<String>,
    pub port: Option<u16>,
    pub pid: Option<u32>,
}

// ---------------------------------------------------------------------------
// BackendState — now owns the Job Object handle
// ---------------------------------------------------------------------------

struct BackendState {
    child: Option<Child>,
    #[cfg(target_os = "windows")]
    job: Option<winjob::JobHandle>,
    port: Option<u16>,
    stage: String,
    message: String,
    error: Option<String>,
}

// ---------------------------------------------------------------------------
// Tauri commands
// ---------------------------------------------------------------------------

#[tauri::command]
fn get_startup_status(
    state: tauri::State<'_, Arc<Mutex<BackendState>>>,
) -> Result<StartupStatus, String> {
    let s = state.lock().map_err(|e| e.to_string())?;
    Ok(StartupStatus {
        stage: s.stage.clone(),
        message: s.message.clone(),
        error: s.error.clone(),
        port: s.port,
        pid: s.child.as_ref().map(|c| c.id()),
    })
}

#[tauri::command]
fn get_backend_port(state: tauri::State<'_, Arc<Mutex<BackendState>>>) -> Result<u16, String> {
    let s = state.lock().map_err(|e| e.to_string())?;
    s.port.ok_or_else(|| "Backend not ready".to_string())
}

// ---------------------------------------------------------------------------
// Path helpers
// ---------------------------------------------------------------------------

fn get_fixly_backend_install_path(app: Option<&AppHandle>) -> Option<std::path::PathBuf> {
    if let Some(handle) = app {
        if let Ok(resource_dir) = handle.path().resource_dir() {
            let p = resource_dir.join("backend").join("backend.exe");
            if p.exists() {
                return p.canonicalize().ok().or(Some(p));
            }
        }
        if let Ok(app_data) = handle.path().app_data_dir() {
            let p = app_data
                .join("..")
                .join("Fixly")
                .join("backend")
                .join("backend.exe");
            if p.exists() {
                return p.canonicalize().ok().or(Some(p));
            }
        }
    }
    if let Ok(local) = std::env::var("LOCALAPPDATA") {
        let p = std::path::PathBuf::from(local)
            .join("Fixly")
            .join("backend")
            .join("backend.exe");
        if p.exists() {
            return p.canonicalize().ok().or(Some(p));
        }
    }
    if let Ok(appdata) = std::env::var("APPDATA") {
        let p = std::path::PathBuf::from(appdata)
            .join("..")
            .join("Local")
            .join("Fixly")
            .join("backend")
            .join("backend.exe");
        if p.exists() {
            return p.canonicalize().ok().or(Some(p));
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Orphan sweep — SAFETY NET for stale processes from previous installs.
// Not the primary kill mechanism (the Job Object handles our own tree).
// ---------------------------------------------------------------------------

fn kill_fixly_orphans(fixly_backend_path: Option<&std::path::Path>) {
    let Some(target) = fixly_backend_path else {
        return;
    };
    let target_canonical = target
        .canonicalize()
        .unwrap_or_else(|_| target.to_path_buf());
    let mut sys = System::new_all();
    sys.refresh_all();
    for (pid, proc_info) in sys.processes() {
        let Some(exe) = proc_info.exe() else { continue };
        let is_exact = exe == target_canonical.as_path();
        let is_fixly_backend = proc_info.name() == "backend.exe"
            && exe.to_string_lossy().contains("Fixly")
            && exe
                .canonicalize()
                .map(|c| c == target_canonical)
                .unwrap_or(false);
        if !is_exact && !is_fixly_backend {
            continue;
        }
        let pid_u32 = pid.as_u32();
        if !proc_info.kill() {
            let _ = std::process::Command::new("taskkill")
                .args(["/PID", &pid_u32.to_string(), "/F"])
                .output();
        }
    }
}

// ---------------------------------------------------------------------------
// File-lock wait — properly handles ERROR_SHARING_VIOLATION (Win32 error 32)
// ---------------------------------------------------------------------------

/// Wait until `path` can be opened for writing, or give up after ~12 seconds.
///
/// On Windows, when a process has the file memory-mapped (e.g. as its own
/// executable), `OpenOptions::write(true)` fails with ERROR_SHARING_VIOLATION
/// (raw error 32). This is retryable — the process may be in the process of
/// exiting and the kernel has not yet released the file mapping.
fn wait_for_backend_unlocked(path: Option<&std::path::Path>) {
    let Some(p) = path else { return };
    let start = Instant::now();
    let timeout = Duration::from_secs(12);
    let mut attempts = 0u32;

    while start.elapsed() < timeout {
        attempts += 1;
        match std::fs::OpenOptions::new().write(true).open(p) {
            Ok(_) => {
                if attempts > 1 {
                    eprintln!(
                        "[Fixly] backend.exe became writable after {}ms ({} attempts)",
                        start.elapsed().as_millis(),
                        attempts
                    );
                }
                return;
            }
            Err(e) => {
                // ERROR_SHARING_VIOLATION (32) — file is locked by another process.
                // Retry until the process exits and the kernel releases the mapping.
                #[cfg(target_os = "windows")]
                {
                    if let Some(32) = e.raw_os_error() {
                        thread::sleep(Duration::from_millis(200));
                        continue;
                    }
                }
                // PermissionDenied — handle not yet released, retry.
                if e.kind() == std::io::ErrorKind::PermissionDenied {
                    thread::sleep(Duration::from_millis(200));
                    continue;
                }
                // File not found or other permanent errors — stop immediately.
                return;
            }
        }
    }
    eprintln!(
        "[Fixly] WARNING: backend.exe still locked after {:?} ({} attempts) — NSIS may fail",
        timeout, attempts
    );
}

// ---------------------------------------------------------------------------
// Backend tree shutdown
// ---------------------------------------------------------------------------

fn kill_backend_tree(state: &Arc<Mutex<BackendState>>, app: Option<&AppHandle>) {
    // 1. Close Job Object (kills ALL processes in the job via kernel) and
    //    kill the tracked child directly — single lock acquisition, no races.
    {
        if let Ok(mut s) = state.lock() {
            // Dropping the Job handle triggers JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
            // The kernel terminates every process assigned to this job — bootloader,
            // PyInstaller grandchild (the actual Python/uvicorn server), and any
            // other descendants — deterministically and without path matching.
            #[cfg(target_os = "windows")]
            {
                if s.job.is_some() {
                    eprintln!("[Fixly] Closing Job Object — killing backend process tree");
                    s.job.take();
                }
            }

            // Belt-and-suspenders: also kill the tracked child directly.
            // This is a no-op if the Job already killed it, and ensures
            // we own the Child handle for proper wait/cleanup.
            if let Some(mut child) = s.child.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }

    // 2. Brief pause for the kernel to release file handles after process
    //    termination. Job Object kills are immediate at the process level,
    //    but the kernel may need a few milliseconds to tear down memory
    //    mappings and close file handles.
    thread::sleep(Duration::from_millis(300));

    // 3. Safety-net orphan sweep — kills any stale backend.exe processes
    //    from previous installs that were never assigned to our Job Object.
    //    Uses strict Fixly path matching; never touches unrelated processes.
    let fixly_path = get_fixly_backend_install_path(app);
    kill_fixly_orphans(fixly_path.as_deref());

    // 4. Wait until backend.exe is actually writable (no SharingViolation).
    wait_for_backend_unlocked(fixly_path.as_deref());
}

fn kill_backend(state: &Arc<Mutex<BackendState>>) {
    kill_backend_tree(state, None);
}

#[tauri::command]
fn shutdown_backend(
    state: tauri::State<'_, Arc<Mutex<BackendState>>>,
    app: AppHandle,
) -> Result<(), String> {
    kill_backend_tree(state.inner(), Some(&app));
    Ok(())
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

fn health_check(port: u16) -> Result<(), String> {
    let addr = format!("127.0.0.1:{}", port);
    let timeout = Duration::from_secs(15);
    let start = Instant::now();

    loop {
        if start.elapsed() > timeout {
            return Err("Backend health check timed out after 15s".to_string());
        }
        let parsed = addr
            .parse()
            .map_err(|e| format!("Invalid address: {}", e))?;
        match TcpStream::connect_timeout(&parsed, Duration::from_secs(2)) {
            Ok(mut stream) => {
                let request =
                    "GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n";
                if stream.write_all(request.as_bytes()).is_err() {
                    thread::sleep(Duration::from_millis(300));
                    continue;
                }
                let mut response = String::new();
                if stream.read_to_string(&mut response).is_err() {
                    thread::sleep(Duration::from_millis(300));
                    continue;
                }
                if response.contains("200 OK") {
                    return Ok(());
                }
                return Err("Backend health check returned non-200 status".to_string());
            }
            Err(_) => {
                thread::sleep(Duration::from_millis(300));
                continue;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Backend discovery
// ---------------------------------------------------------------------------

fn find_backend_exe(app: &AppHandle) -> Option<std::path::PathBuf> {
    #[cfg(debug_assertions)]
    {
        let dev_exe = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..")
            .join("backend")
            .join("dist")
            .join("backend.exe");
        if dev_exe.exists() {
            return Some(dev_exe);
        }
    }

    let resource_dir = app.path().resource_dir().ok()?;
    let exe_path = resource_dir.join("backend").join("backend.exe");
    if exe_path.exists() {
        return Some(exe_path);
    }
    None
}

fn find_python() -> Option<String> {
    let candidates = if cfg!(target_os = "windows") {
        vec!["pythonw.exe", "python.exe", "py.exe"]
    } else {
        vec!["python3", "python"]
    };

    for name in &candidates {
        if let Ok(output) = Command::new(name).arg("--version").output() {
            if output.status.success() {
                return Some(name.to_string());
            }
        }
    }
    None
}

fn find_backend_dir(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    #[cfg(debug_assertions)]
    {
        let dev_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..")
            .join("..")
            .join("backend");
        if dev_path.exists() {
            return Ok(dev_path
                .canonicalize()
                .map_err(|e| format!("Cannot resolve backend path: {}", e))?);
        }
    }

    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|e| format!("Cannot get resource dir: {}", e))?;
    let prod_path = resource_dir.join("backend");
    if prod_path.exists() {
        return Ok(prod_path);
    }

    Err(
        "Backend directory not found. Reinstall Fixly or verify backend files are present."
            .to_string(),
    )
}

// ---------------------------------------------------------------------------
// Env / permissions helpers
// ---------------------------------------------------------------------------

fn restrict_file_permissions(path: &std::path::Path) {
    #[cfg(target_os = "windows")]
    {
        let path_str = path.to_string_lossy();
        let _ = std::process::Command::new("icacls")
            .args([
                &*path_str,
                "/inheritance:r",
                "/grant",
                &*format!("%USERNAME%:F"),
            ])
            .output();
    }
    #[cfg(not(target_os = "windows"))]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600));
    }
}

fn ensure_env_file(app: &AppHandle) -> Option<std::path::PathBuf> {
    let app_data = app.path().app_data_dir().ok()?;
    let env_path = app_data.join(".env");

    if env_path.exists() {
        return Some(env_path);
    }

    let resource_dir = app.path().resource_dir().ok()?;
    let bundled_default = resource_dir.join("backend").join(".env.default");
    if bundled_default.exists() {
        if let Err(e) = std::fs::create_dir_all(&app_data) {
            eprintln!("Failed to create app data dir: {}", e);
            return None;
        }
        if let Err(e) = std::fs::copy(&bundled_default, &env_path) {
            eprintln!("Failed to copy default .env: {}", e);
            return None;
        }
        restrict_file_permissions(&env_path);
        return Some(env_path);
    }

    None
}

// ---------------------------------------------------------------------------
// Stdout drain
// ---------------------------------------------------------------------------

fn drain_backend_stdout(mut reader: BufReader<std::process::ChildStdout>) {
    thread::spawn(move || {
        let mut buf = String::new();
        loop {
            buf.clear();
            match reader.read_line(&mut buf) {
                Ok(0) | Err(_) => break,
                Ok(_) => {}
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Backend startup
// ---------------------------------------------------------------------------

/// Spawn the backend process and assign it to a Windows Job Object so that ALL
/// descendants (including the PyInstaller grandchild) are killed when we close
/// the job handle.
fn start_backend_exe(
    app: AppHandle,
    state: Arc<Mutex<BackendState>>,
    exe_path: std::path::PathBuf,
) {
    {
        if let Ok(mut s) = state.lock() {
            s.stage = "starting_backend".to_string();
            s.message = "Starting backend executable...".to_string();
        }
    }

    let parent_dir = exe_path.parent().unwrap_or(&exe_path).to_path_buf();

    let env_file = ensure_env_file(&app);

    let mut cmd = Command::new(&exe_path);
    cmd.arg("0");
    cmd.current_dir(&parent_dir);
    if let Some(env) = &env_file {
        cmd.env("FIXLY_ENV_FILE", env);
    }
    // Point the backend at the bundled embedding model so document
    // search works offline on fresh installs (no Hugging Face download).
    // Layout mirrors tauri.conf.json resources: backend/models/embeddings.
    if let Ok(resource_dir) = app.path().resource_dir() {
        let emb = resource_dir.join("backend").join("models").join("embeddings");
        if emb.join("all-MiniLM-L6-v2").join("config.json").exists() {
            cmd.env("FIXLY_EMBEDDINGS_DIR", &emb);
        }
    }
    // Keep user uploads outside the install resources dir so app updates
    // never wipe them and the frozen backend never writes into TEMP.
    if let Ok(app_data) = app.path().app_data_dir() {
        let uploads = app_data.join("uploads").join("documents");
        let _ = std::fs::create_dir_all(&uploads);
        cmd.env("FIXLY_UPLOAD_DIR", &uploads);
    }
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    #[cfg(target_os = "windows")]
    {
        cmd.creation_flags(CREATE_NO_WINDOW);
    }

    let mut child = match cmd.spawn() {
        Ok(c) => c,
        Err(e) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Failed to start backend executable".to_string();
                s.error = Some(format!("Could not launch backend.exe: {}", e));
            }
            return;
        }
    };

    // ---- Windows Job Object: assign the child to a kill-on-close job ----
    #[cfg(target_os = "windows")]
    {
        let raw_handle = child.as_raw_handle();
        if let Some(job) = winjob::JobHandle::create() {
            if job.set_kill_on_close() {
                if job.assign_process(raw_handle) {
                    eprintln!(
                        "[Fixly] Job Object created — PID {} assigned (grandchild will be killed on close)",
                        child.id()
                    );
                    if let Ok(mut s) = state.lock() {
                        s.job = Some(job);
                    }
                } else {
                    eprintln!(
                        "[Fixly] WARNING: AssignProcessToJobObject failed (errno {}) — orphan sweep will be primary kill",
                        std::io::Error::last_os_error()
                    );
                }
            } else {
                eprintln!("[Fixly] WARNING: SetInformationJobObject failed — orphan sweep will be primary kill");
            }
        } else {
            eprintln!(
                "[Fixly] WARNING: CreateJobObjectW failed — orphan sweep will be primary kill"
            );
        }
    }

    let stdout = child.stdout.take();
    {
        if let Ok(mut s) = state.lock() {
            s.child = Some(child);
        }
    }

    let mut reader = match stdout {
        Some(out) => BufReader::new(out),
        None => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Failed to capture backend output".to_string();
            }
            return;
        }
    };

    let mut port: Option<u16> = None;
    loop {
        let mut line = String::new();
        match reader.read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => {
                let trimmed = line.trim_end();
                if let Some(port_str) = trimmed.strip_prefix("FIXLY_PORT:") {
                    if let Ok(p) = port_str.trim().parse::<u16>() {
                        port = Some(p);
                        if let Ok(mut s) = state.lock() {
                            s.port = Some(p);
                            s.stage = "waiting_health".to_string();
                            s.message = format!("Backend starting on port {}...", p);
                        }
                        break;
                    }
                }
            }
            Err(_) => {
                if let Ok(mut s) = state.lock() {
                    s.stage = "error".to_string();
                    s.message = "Backend output error".to_string();
                    s.error = Some("Failed to read backend process output.".to_string());
                }
                return;
            }
        }
    }

    let port = match port {
        Some(p) => {
            drain_backend_stdout(reader);
            p
        }
        None => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend port not detected".to_string();
                s.error = Some("The backend executable did not report its port.".to_string());
            }
            return;
        }
    };

    {
        if let Ok(mut s) = state.lock() {
            s.stage = "waiting_health".to_string();
            s.message = format!("Waiting for backend health check on port {}...", port);
        }
    }

    match health_check(port) {
        Ok(_) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "ready".to_string();
                s.message = format!("Backend ready on port {}", port);
            }
        }
        Err(e) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend health check failed".to_string();
                s.error = Some(e);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Backend startup — Python fallback
// ---------------------------------------------------------------------------

fn start_backend(app: AppHandle, state: Arc<Mutex<BackendState>>) {
    if let Some(exe_path) = find_backend_exe(&app) {
        return start_backend_exe(app, state, exe_path);
    }

    let python = match find_python() {
        Some(p) => p,
        None => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend executable not found".to_string();
                s.error = Some("Could not find backend.exe or Python 3.11+. Reinstall Fixly or install Python from python.org.".to_string());
            }
            return;
        }
    };

    let backend_dir = match find_backend_dir(&app) {
        Ok(d) => d,
        Err(e) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend not found".to_string();
                s.error = Some(e);
            }
            return;
        }
    };

    {
        if let Ok(mut s) = state.lock() {
            s.stage = "starting_backend".to_string();
            s.message = "Starting backend server (Python)...".to_string();
        }
    }

    let mut cmd = Command::new(&python);
    cmd.arg("-m");
    cmd.arg("app.main");
    cmd.arg("0");
    cmd.current_dir(&backend_dir);
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    #[cfg(target_os = "windows")]
    {
        cmd.creation_flags(CREATE_NO_WINDOW);
    }

    let mut child = match cmd.spawn() {
        Ok(c) => c,
        Err(e) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Failed to start backend".to_string();
                s.error = Some(format!("Could not start Python backend: {}", e));
            }
            return;
        }
    };

    // ---- Windows Job Object for Python fallback path ----
    #[cfg(target_os = "windows")]
    {
        let raw_handle = child.as_raw_handle();
        if let Some(job) = winjob::JobHandle::create() {
            if job.set_kill_on_close() && job.assign_process(raw_handle) {
                if let Ok(mut s) = state.lock() {
                    s.job = Some(job);
                }
            }
        }
    }

    let stdout = child.stdout.take();
    {
        if let Ok(mut s) = state.lock() {
            s.child = Some(child);
        }
    }

    let mut reader = match stdout {
        Some(out) => BufReader::new(out),
        None => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Failed to capture backend output".to_string();
            }
            return;
        }
    };

    let mut port: Option<u16> = None;
    loop {
        let mut line = String::new();
        match reader.read_line(&mut line) {
            Ok(0) => break,
            Ok(_) => {
                let trimmed = line.trim_end();
                if let Some(port_str) = trimmed.strip_prefix("FIXLY_PORT:") {
                    if let Ok(p) = port_str.trim().parse::<u16>() {
                        port = Some(p);
                        if let Ok(mut s) = state.lock() {
                            s.port = Some(p);
                            s.stage = "waiting_health".to_string();
                            s.message = format!("Backend starting on port {}...", p);
                        }
                        break;
                    }
                }
            }
            Err(_) => {
                if let Ok(mut s) = state.lock() {
                    s.stage = "error".to_string();
                    s.message = "Backend output error".to_string();
                }
                return;
            }
        }
    }

    let port = match port {
        Some(p) => {
            drain_backend_stdout(reader);
            p
        }
        None => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend port not detected".to_string();
                s.error = Some(
                    "The backend did not report its port. Verify the backend installation."
                        .to_string(),
                );
            }
            return;
        }
    };

    {
        if let Ok(mut s) = state.lock() {
            s.stage = "waiting_health".to_string();
            s.message = format!("Waiting for backend health check on port {}...", port);
        }
    }

    match health_check(port) {
        Ok(_) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "ready".to_string();
                s.message = format!("Backend ready on port {}", port);
            }
        }
        Err(e) => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend health check failed".to_string();
                s.error = Some(e);
            }
        }
    }
}

// ---------------------------------------------------------------------------
// App entry point
// ---------------------------------------------------------------------------

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|_app, _args, _cwd| {}))
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            if let Err(e) = app.deep_link().register_all() {
                eprintln!("failed to register fixly:// deep link: {}", e);
            }

            let backend_state = Arc::new(Mutex::new(BackendState {
                child: None,
                #[cfg(target_os = "windows")]
                job: None,
                port: None,
                stage: "initializing".to_string(),
                message: "Initializing...".to_string(),
                error: None,
            }));
            let state_clone = backend_state.clone();
            app.manage(backend_state);

            let app_handle = app.handle().clone();
            thread::spawn(move || {
                start_backend(app_handle, state_clone);
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_startup_status,
            get_backend_port,
            shutdown_backend
        ])
        .build(tauri::generate_context!())
        .expect("error while building Fixly")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                let state: tauri::State<'_, Arc<Mutex<BackendState>>> = app_handle.state();
                kill_backend(state.inner());
            }
        });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod shutdown_tests {
    use super::*;

    fn empty_state() -> Arc<Mutex<BackendState>> {
        Arc::new(Mutex::new(BackendState {
            child: None,
            #[cfg(target_os = "windows")]
            job: None,
            port: None,
            stage: String::new(),
            message: String::new(),
            error: None,
        }))
    }

    #[test]
    fn kill_backend_is_idempotent_on_empty_state() {
        let s = empty_state();
        kill_backend(&s);
        kill_backend(&s);
        let locked = s.lock().unwrap();
        assert!(locked.child.is_none());
        #[cfg(target_os = "windows")]
        assert!(locked.job.is_none());
    }

    #[test]
    fn kill_backend_tree_is_idempotent_without_app() {
        let s = empty_state();
        kill_backend_tree(&s, None);
        kill_backend_tree(&s, None);
        let locked = s.lock().unwrap();
        assert!(locked.child.is_none());
        #[cfg(target_os = "windows")]
        assert!(locked.job.is_none());
    }

    #[test]
    fn get_fixly_backend_path_returns_option_without_panic() {
        let _ = get_fixly_backend_install_path(None);
    }

    #[test]
    fn kill_orphans_with_none_is_noop() {
        kill_fixly_orphans(None);
        wait_for_backend_unlocked(None);
    }

    #[test]
    fn kill_orphans_never_kills_unrelated_backend_exe() {
        let fake = std::path::Path::new("C:\\Windows\\System32\\not_fixly_backend.exe");
        kill_fixly_orphans(Some(fake));
    }

    // ---- Windows Job Object tests ----

    #[cfg(target_os = "windows")]
    mod job_tests {
        use super::*;

        #[test]
        fn job_create_and_drop_succeeds() {
            let job = winjob::JobHandle::create();
            assert!(job.is_some(), "CreateJobObjectW should succeed");
            // Drop happens automatically — no panic, no leak
        }

        #[test]
        fn job_set_kill_on_close_succeeds() {
            let job = winjob::JobHandle::create().unwrap();
            assert!(
                job.set_kill_on_close(),
                "SetInformationJobObject with KILL_ON_JOB_CLOSE should succeed"
            );
        }

        #[test]
        fn job_assign_real_process() {
            // Spawn a child process and assign it to the job
            let mut child = Command::new("cmd.exe")
                .args(["/C", "timeout /t 30 /nobreak >nul"])
                .stdout(std::process::Stdio::piped())
                .stderr(std::process::Stdio::piped())
                .spawn()
                .expect("failed to spawn cmd.exe");

            let raw_handle = child.as_raw_handle();

            let job = winjob::JobHandle::create().unwrap();
            assert!(job.set_kill_on_close());
            assert!(
                job.assign_process(raw_handle),
                "AssignProcessToJobObject should succeed for our own child"
            );

            // Drop the job — this should kill the child via KILL_ON_JOB_CLOSE
            drop(job);

            // Give the kernel a moment to terminate the process
            let start = Instant::now();
            let status = child.wait().expect("wait should succeed");
            let elapsed = start.elapsed();

            // Process should have been killed quickly (well under the 30s timeout)
            assert!(
                elapsed < Duration::from_secs(5),
                "Job Object should kill child within 5s, took {:?}",
                elapsed
            );
        }

        #[test]
        fn job_kills_grandchild_process_tree() {
            // This test demonstrates that the Job Object kills the GRANDCHILD
            // (PyInstaller's Python process) in addition to the tracked child.
            //
            // Process tree:
            //   parent (cmd.exe) → child (cmd.exe) → grandchild (cmd.exe)
            //
            // Killing only the parent leaves the grandchild alive.
            // The Job Object kills both.

            // Spawn: cmd.exe /C cmd.exe /C timeout /t 30 /nobreak
            // This creates: cmd.exe → cmd.exe → timeout.exe
            let mut parent = Command::new("cmd.exe")
                .args(["/C", "cmd.exe", "/C", "timeout /t 30 /nobreak >nul"])
                .stdout(std::process::Stdio::piped())
                .stderr(std::process::Stdio::piped())
                .spawn()
                .expect("failed to spawn parent cmd.exe");

            // Wait a moment for the grandchild to start
            thread::sleep(Duration::from_millis(1000));

            // Capture the parent's PID
            let parent_pid = parent.id();

            // Find any child processes of the parent
            let output_before = std::process::Command::new("cmd.exe")
                .args([
                    "/C",
                    "wmic",
                    "process",
                    "where",
                    &format!("ParentProcessId={}", parent_pid),
                    "get",
                    "ProcessId,Name",
                    "/format:list",
                ])
                .output()
                .expect("wmic failed");

            let stdout_before = String::from_utf8_lossy(&output_before.stdout);
            let has_grandchild = stdout_before.contains("ProcessId=");

            if has_grandchild {
                // Assign the parent to a Job Object with kill-on-close
                let raw_handle = parent.as_raw_handle();
                let job = winjob::JobHandle::create().unwrap();
                assert!(job.set_kill_on_close());
                assert!(job.assign_process(raw_handle));

                // Drop the job — kills parent AND grandchild
                drop(job);
                thread::sleep(Duration::from_millis(500));

                // Verify no descendants remain
                let output_after = std::process::Command::new("cmd.exe")
                    .args([
                        "/C",
                        "wmic",
                        "process",
                        "where",
                        &format!("ParentProcessId={}", parent_pid),
                        "get",
                        "ProcessId",
                        "/format:list",
                    ])
                    .output()
                    .expect("wmic failed");

                let stdout_after = String::from_utf8_lossy(&output_after.stdout);
                assert!(
                    !stdout_after.contains("ProcessId="),
                    "Grandchild should have been killed by Job Object"
                );
            }

            // Clean up parent
            let _ = parent.kill();
            let _ = parent.wait();
        }
    }

    // ---- wait_for_backend_unlocked tests ----

    #[test]
    fn wait_for_backend_unlocked_returns_immediately_when_none() {
        // Should not block or panic when path is None
        wait_for_backend_unlocked(None);
    }

    #[test]
    fn wait_for_backend_unlocked_returns_for_nonexistent_file() {
        // File does not exist — should return immediately (not loop for 12s)
        let start = Instant::now();
        wait_for_backend_unlocked(Some(std::path::Path::new("C:\\nonexistent\\backend.exe")));
        assert!(
            start.elapsed() < Duration::from_secs(2),
            "Should return quickly for nonexistent file"
        );
    }
}
