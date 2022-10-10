with import <nixpkgs> {};
with pkgs.python3Packages;

let

  mutwo-core-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.core/archive/97aea97f996973955889630c437ceaea405ea0a7.tar.gz";
  mutwo-core = import (mutwo-core-archive + "/default.nix");

  mutwo-music-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.music/archive/4e4369c1c9bb599f47ec65eb86f87e9179e17d97.tar.gz";
  mutwo-music = import (mutwo-music-archive + "/default.nix");

  mutwo-mbrola-archive = builtins.fetchTarball "https://github.com/mutwo-org/mutwo.mbrola/archive/ffd2ee601e8bb28cc9201c43811fd2b5334c06de.tar.gz";
  mutwo-mbrola = import (mutwo-mbrola-archive + "/default.nix");

  walkman-archive = builtins.fetchTarball "https://github.com/audiowalkman/walkman/archive/1f86d4b75e756a64eddafd381c7c688d3cf5e15d.tar.gz";
  walkman = import (walkman-archive + "/default.nix");

  mutwo-9-4 = pkgs.python39Packages.buildPythonPackage rec {
    name = "mutwo.c9p4";
    src = ./mutwo.c9p4;
    buildInputs = [ mbrola ];
    checkInputs = [ mbrola ];
    propagatedBuildInputs = with pkgs; [
        mutwo-core
        mutwo-music
        mutwo-mbrola
        python39Packages.jinja2
    ];
    doCheck = true;
  };

  walkman-modules-9-4 = pkgs.python39Packages.buildPythonPackage rec {
    name = "walkman_modules.c9p4";
    src = ./walkman_modules.c9p4;
    buildInputs = [ walkman ];
    checkInputs = [ walkman ];
    propagatedBuildInputs = with pkgs; [
        walkman
    ];
    doCheck = true;
  };

  python-9-4 = pkgs.python39.buildEnv.override {
    extraLibs = with pkgs; [
      python39Packages.ipython
      mutwo-9-4
      walkman
      walkman-modules-9-4
    ];
  };

in

  pkgs.mkShell {
    buildInputs = with pkgs; [
      # version control
      git
      # python with relevant packages
      python-9-4
      mbrola
    ];
  }
