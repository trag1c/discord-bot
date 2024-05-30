{
  description = "Ghostty discord bot";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    zig.url = "github:mitchellh/zig-overlay";

    # We use unstable because some of our Python dependencies require the
    # cutting edge. We just have to be careful about updating our pin.
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";

    # We always want to use the latest to get the latest overrides.
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };

    # Used for shell.nix
    flake-compat = { url = github:edolstra/flake-compat; flake = false; };
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
    let
      overlays = [
        # Our repo overlay
        (import ./nix/overlay.nix)

        # poetry2nix overlay
        inputs.poetry2nix.overlays.default
      ];

      # Our supported systems are the same supported systems as the Zig binaries
      systems = builtins.attrNames inputs.zig.packages;
    in flake-utils.lib.eachSystem systems (system:
      let pkgs = import nixpkgs { inherit overlays system; };
      in rec {
        devShell = pkgs.devShell;

        packages.app = pkgs.app;
        defaultPackage = packages.app;
        legacyPackages = pkgs;
      }
    );
}
