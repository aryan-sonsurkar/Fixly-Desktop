use tauri::Manager;

#[tauri::command]
fn get_backend_port() -> u16 {
    8000
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .invoke_handler(tauri::generate_handler![get_backend_port])
        .setup(|app| {
            let _window = app.get_webview_window("main").unwrap();
            
            // Deep link handler for custom URL schemes (e.g., fixly://auth/callback)
            #[cfg(desktop)]
            {
                let app_handle = app.handle().clone();
                app.set_uri_scheme_protocol_handler("fixly", move |_app, uri| {
                    log::info!("Deep link received: {}", uri);
                    // Emit event to frontend to handle the deep link
                    if let Err(e) = app_handle.emit("deep-link", uri.to_string()) {
                        log::error!("Failed to emit deep-link event: {}", e);
                    }
                })?;
            }
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Fixly");
}
