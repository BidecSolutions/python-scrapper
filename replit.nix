{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.virtualenv
  ];
  # For Python projects, Replit automatically installs dependencies from requirements.txt
  # You can also specify a custom build command if needed
}

