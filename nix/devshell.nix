{ mkShell, lib, stdenv

# Deps
, poetry
, python3

# Our app
, pythonApp
}:
let
  rpathLibs = [
    # None yet
  ] ++ lib.optionals stdenv.isLinux [
    # None yet
  ];

in mkShell rec {
  name = "ghostty-discord-bot";

  nativeBuildInputs = [
    # Python lib
    python3
    poetry
  ] ++ lib.optionals stdenv.isLinux [
    # None yet
  ];

  buildInputs = rpathLibs;# ++ [ pythonApp.devEnv ];

  # This should be set onto the rpath of the ghostty binary if you want
  # it to be "portable" across the system.
  LD_LIBRARY_PATH = lib.makeLibraryPath rpathLibs;
  DYLD_LIBRARY_PATH = lib.makeLibraryPath rpathLibs;
}
