use std::fs::{self, File};
use std::io::Write;
use std::process::Command;

// Simple integration test: create temp dir with 3 files, run pp-split, expect batch_001 exists
#[test]
fn creates_batch_folder_and_moves_files() {
    let tmp = tempfile::tempdir().unwrap();
    let dir = tmp.path();

    // Create a few dummy files
    for i in 0..3 {
        let mut f = File::create(dir.join(format!("file_{}.dat", i))).unwrap();
        writeln!(f, "dummy").unwrap();
    }

    // Run pp-split on temp dir via cargo run
    let status = Command::new("cargo")
        .args(["run", "--quiet", "--bin", "pp-split", dir.to_str().unwrap()])
        .status()
        .expect("failed to run pp-split");
    assert!(status.success());

    // Verify batch folder exists and files moved
    let batch = dir.join("batch_001");
    assert!(batch.is_dir());
    let entries: Vec<_> = fs::read_dir(batch).unwrap().collect();
    assert_eq!(entries.len(), 3);
}
