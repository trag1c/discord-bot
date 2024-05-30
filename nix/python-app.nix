{ poetry2nix
, lib
, stdenv
, substituteAll
, writeShellScriptBin

, python3
}:

let
  overrides = poetry2nix.overrides.withDefaults (self: super: {
    # None yet
  });
in {
  # This is the main runnable app that only includes runtime dependencies.
  app = poetry2nix.mkPoetryApplication {
    projectDir = ./..;
    overrides = overrides;
  };

  # This is the development environment.
  devEnv = poetry2nix.mkPoetryEnv {
    projectDir = ./..;
    overrides = overrides;
  };
}
