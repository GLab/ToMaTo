#!/bin/bash

export PATH="$PATH:/root/.cargo/bin"
rustup default nightly
cargo run --release --manifest-path /code/service/Cargo.toml /etc/tomato/config.yaml
