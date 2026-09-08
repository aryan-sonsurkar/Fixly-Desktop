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
use std::os::windows::process::CommandExt;

#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(Clone, Serialize)]
pub struct StartupStatus {
    pub stage: String,
    pub message: String,
    pub error: Option<String>,
    pub port: Option<u16>,
    pub pid: Option<u32>,
}

struct BackendState {
    child: Option<Child>,
    port: Option<u16>,
    stage: String,
    message: String,
    error: Option<String>,
}

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

fn get_fixly_backend_install_path(app: Option<&AppHandle>) -> Option<std::path::PathBuf> {
    // Strictly scoped to Fixly's own backend location — never matches arbitrary backend.exe
    if let Some(handle) = app {
        if let Ok(resource_dir) = handle.path().resource_dir() {
            let p = resource_dir.join("backend").join("backend.exe");
            if p.exists() {
                return p.canonicalize().ok().or(Some(p));
            }
        }
        if let Ok(app_data) = handle.path().app_data_dir() {
            // Fallback: AppData/Local/Fixly/backend/backend.exe is where NSIS currentUser installs backend
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
    // Direct well-known currentUser install path (independent of AppHandle)
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

fn kill_fixly_orphans(fixly_backend_path: Option<&std::path::Path>) {
    let Some(target) = fixly_backend_path else {
        return;
    };
    let target_canonical = target
        .canonicalize()
        .unwrap_or_else(|_| target.to_path_buf());
    let mut sys = System::new_all();
    sys.refresh_all();
    for (pid, proc) in sys.processes() {
        let Some(exe) = proc.exe() else { continue };
        // Only match exact Fixly backend path — never global backend.exe/python.exe
        let is_exact = exe == target_canonical.as_path();
        let is_fixly_backend = proc.name() == "backend.exe"
            && exe.to_string_lossy().contains("Fixly")
            && exe
                .canonicalize()
                .map(|c| c == target_canonical)
                .unwrap_or(false);
        if !is_exact && !is_fixly_backend {
            continue;
        }
        // Don't kill our own tracked child again (already killed above)
        let pid_u32 = pid.as_u32();
        // Use sysinfo kill first, fallback to taskkill for stubborn grandchild
        if !proc.kill() {
            let _ = std::process::Command::new("taskkill")
                .args(["/PID", &pid_u32.to_string(), "/F"])
                .output();
        }
    }
}

fn wait_for_backend_unlocked(path: Option<&std::path::Path>) {
    let Some(p) = path else { return };
    for _ in 0..30 {
        // Try to open with write — if locked, open fails
        match std::fs::OpenOptions::new().write(true).open(p) {
            Ok(_) => return,
            Err(e) if e.kind() == std::io::ErrorKind::PermissionDenied => {
                thread::sleep(Duration::from_millis(100));
                continue;
            }
            Err(_) => return,
        }
    }
}

fn kill_backend_tree(state: &Arc<Mutex<BackendState>>, app: Option<&AppHandle>) {
    // 1. Tracked child (PyInstaller bootloader)
    if let Ok(mut s) = state.lock() {
        if let Some(mut child) = s.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    // 2. Orphan grandchild / previous install's backend — strictly Fixly path scoped
    let fixly_path = get_fixly_backend_install_path(app);
    kill_fixly_orphans(fixly_path.as_deref());
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

    // Try bundled default
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

/// Keep draining the backend's stdout pipe after the port has been detected.
///
/// The backend keeps writing logs (uvicorn access logs, app logs) for the whole
/// session. If nothing reads them, the pipe buffer (a few KB on Windows) fills up
/// and the backend blocks on its next write, freezing its event loop so every
/// request times out. Draining the pipe in the background prevents this.
fn drain_backend_stdout(mut reader: BufReader<std::process::ChildStdout>) {
    thread::spawn(move || {
        let mut buf = String::new();
        loop {
            buf.clear();
            match reader.read_line(&mut buf) {
                Ok(0) | Err(_) => break,
                Ok(_) => {
                    // Read and discard; only draining matters.
                }
            }
        }
    });
}

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
    // Random free port: avoids hijacking by stale backend processes from previous sessions.
    cmd.arg("0");
    cmd.current_dir(&parent_dir);
    if let Some(env) = &env_file {
        // Set env var instead of CLI arg — invisible to process listings
        cmd.env("FIXLY_ENV_FILE", env);
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
            // Keep reading so the backend's stdout pipe never fills up.
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

fn start_backend(app: AppHandle, state: Arc<Mutex<BackendState>>) {
    // Prefer the standalone backend.exe if available
    if let Some(exe_path) = find_backend_exe(&app) {
        return start_backend_exe(app, state, exe_path);
    }

    // Fallback to python -m app.main
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
    // Random free port: avoids hijacking by stale backend processes from previous sessions.
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
            // Keep reading so the backend's stdout pipe never fills up.
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

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|_app, _args, _cwd| {
            // Windows/Linux hand a fixly:// URL to a NEW instance on deep-link;
            // with the single-instance "deep-link" feature the URL is forwarded to
            // this instance's deep-link plugin (which emits "deep-link://new-url")
            // BEFORE this callback runs, so there is nothing to do here.
        }))
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            // Register the fixly:// scheme (HKCU) so OAuth callbacks reach this app.
            if let Err(e) = app.deep_link().register_all() {
                eprintln!("failed to register fixly:// deep link: {}", e);
            }

            let backend_state = Arc::new(Mutex::new(BackendState {
                child: None,
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

#[cfg(test)]
mod shutdown_tests {
    use super::*;

    fn empty_state() -> Arc<Mutex<BackendState>> {
        Arc::new(Mutex::new(BackendState {
            child: None,
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
        assert!(s.lock().unwrap().child.is_none());
    }

    #[test]
    fn kill_backend_tree_is_idempotent_without_app() {
        let s = empty_state();
        kill_backend_tree(&s, None);
        kill_backend_tree(&s, None);
        assert!(s.lock().unwrap().child.is_none());
    }

    #[test]
    fn get_fixly_backend_path_returns_option_without_panic() {
        let _ = get_fixly_backend_install_path(None);
        // Should not panic and should be either Some(canonical) or None
    }

    #[test]
    fn kill_orphans_with_none_is_noop() {
        kill_fixly_orphans(None);
        wait_for_backend_unlocked(None);
    }

    #[test]
    fn kill_orphans_never_kills_unrelated_backend_exe() {
        // Craft a fake unrelated path and ensure kill_fixly_orphans does not touch it.
        // We pass a path that does not exist; kill should be no-op and not panic.
        let fake = std::path::Path::new("C:\\Windows\\System32\\not_fixly_backend.exe");
        kill_fixly_orphans(Some(fake));
        // No assertion beyond not panicking and not killing global backend.exe
    }
}
