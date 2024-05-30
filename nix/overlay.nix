final: prev: rec {
  # Notes:
  #
  # When determining a SHA256, use this to set a fake one until we know
  # the real value:
  #
  #    vendorSha256 = nixpkgs.lib.fakeSha256;
  #

  # Our custom packages related directly to our application
  devShell = prev.callPackage ./devshell.nix { };
  pythonApp = prev.callPackage ./python-app.nix { };
  app = prev.callPackage ./package.nix { };
}
