use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use serde::Serialize;
use tauri::{AppHandle, Manager, RunEvent};

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
fn get_startup_status(state: tauri::State<'_, Arc<Mutex<BackendState>>>) -> Result<StartupStatus, String> {
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

fn kill_backend(state: &Arc<Mutex<BackendState>>) {
    if let Ok(mut s) = state.lock() {
        if let Some(mut child) = s.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

fn health_check(port: u16) -> Result<(), String> {
    let addr = format!("127.0.0.1:{}", port);
    let timeout = Duration::from_secs(15);
    let start = Instant::now();

    loop {
        if start.elapsed() > timeout {
            return Err("Backend health check timed out after 15s".to_string());
        }
        let parsed = addr.parse().map_err(|e| format!("Invalid address: {}", e))?;
        match TcpStream::connect_timeout(&parsed, Duration::from_secs(2)) {
            Ok(mut stream) => {
                let request = "GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n";
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

    let resource_dir = app
        .path()
        .resource_dir()
        .ok()?;
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

    Err("Backend directory not found. Reinstall Fixly or verify backend files are present.".to_string())
}

fn start_backend_exe(_app: AppHandle, state: Arc<Mutex<BackendState>>, exe_path: std::path::PathBuf) {
    {
        if let Ok(mut s) = state.lock() {
            s.stage = "starting_backend".to_string();
            s.message = "Starting backend executable...".to_string();
        }
    }

    let parent_dir = exe_path.parent().unwrap_or(&exe_path).to_path_buf();

    let mut cmd = Command::new(&exe_path);
    cmd.current_dir(&parent_dir);
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

    let reader = match stdout {
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
    for line in reader.lines() {
        match line {
            Ok(line) => {
                if let Some(port_str) = line.strip_prefix("FIXLY_PORT:") {
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
        Some(p) => p,
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

    let reader = match stdout {
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
    for line in reader.lines() {
        match line {
            Ok(line) => {
                if let Some(port_str) = line.strip_prefix("FIXLY_PORT:") {
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
        Some(p) => p,
        None => {
            if let Ok(mut s) = state.lock() {
                s.stage = "error".to_string();
                s.message = "Backend port not detected".to_string();
                s.error = Some("The backend did not report its port. Verify the backend installation.".to_string());
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
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .setup(|app| {
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
        .invoke_handler(tauri::generate_handler![get_startup_status, get_backend_port])
        .build(tauri::generate_context!())
        .expect("error while building Fixly")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                let state: tauri::State<'_, Arc<Mutex<BackendState>>> = app_handle.state();
                kill_backend(state.inner());
            }
        });
}
