{ pkgs }: {
  deps = [
    pkgs.python312Full
    pkgs.replitPackages.prybar-python312
    pkgs.replitPackages.stderred
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.replitPackages.prybar-python312
      pkgs.replitPackages.stderred
    ];
    PYTHONHOME = "${pkgs.python312Full}";
    PYTHONPATH = "$PYTHONPATH:/home/runner/${pkgs.lib.makeSearchPath "site-packages" [
      pkgs.python312Full
    ]}";
  };
}

