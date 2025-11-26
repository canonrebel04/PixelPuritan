use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <directory_path>", args[0]);
        process::exit(1);
    }

    let source_dir = &args[1];
    let path = Path::new(source_dir);

    if !path.is_dir() {
        eprintln!("Error: {} is not a directory.", source_dir);
        process::exit(1);
    }

    // Collect loose files only (ignore existing batch folders)
    let mut files: Vec<PathBuf> = match fs::read_dir(path) {
        Ok(rd) => rd
            .filter_map(|entry| entry.ok())
            .map(|entry| entry.path())
            .collect(),
        Err(e) => {
            eprintln!("Failed to read directory {}: {}", source_dir, e);
            process::exit(2);
        }
    };
    .filter(|p| {
        if !p.is_file() { return false; }
        if let Some(parent) = p.parent() {
            if let Some(parent_name) = parent.file_name() {
                let name_str = parent_name.to_string_lossy();
                if name_str.starts_with("batch_") { return false; }
            }
        }
        true
    })
    .collect();

    if files.is_empty() {
        println!("No loose files found to split.");
        return;
    }

    files.sort();
    let chunk_size = 1000;

    // Resume logic: find next available batch index
    let mut batch_idx = 1;
    while path.join(format!("batch_{:03}", batch_idx)).exists() {
        batch_idx += 1;
    }

    println!("Found {} files. Resuming split at batch_{:03}...", files.len(), batch_idx);

    for chunk in files.chunks(chunk_size) {
        let batch_folder_name = format!("batch_{:03}", batch_idx);
        let batch_path = path.join(&batch_folder_name);

        if let Err(e) = fs::create_dir_all(&batch_path) {
            eprintln!("Failed to create {:?}: {}", batch_path, e);
            continue;
        }

        for file_path in chunk {
            if let Some(file_name) = file_path.file_name() {
                let dest_path = batch_path.join(file_name);
                if let Err(e) = fs::rename(file_path, &dest_path) {
                    eprintln!("Failed to move {:?} to {:?}: {}", file_path, dest_path, e);
                }
            }
        }
        println!("Processed {}: {} images.", batch_folder_name, chunk.len());
        batch_idx += 1;
    }
}
