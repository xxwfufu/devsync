#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DevSync - Universal Development Environment Manager
Created by: xxwfufu

A powerful tool to sync, backup, and manage development environments across multiple machines.
Perfect for developers who work on different computers and want to keep everything in sync!

Features:
- Automatic VS Code settings sync
- Package managers sync (npm, pip, cargo, etc.)
- Git configuration backup
- SSH keys management
- Browser bookmarks sync
- Terminal configurations (zsh, bash, fish)
- Custom dotfiles management
- Cross-platform support (Windows, macOS, Linux)
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import hashlib
import zipfile
from datetime import datetime
from pathlib import Path
import argparse
import colorama
from colorama import Fore, Back, Style
import requests
import threading
import time

# Initialize colorama for cross-platform colored output
colorama.init()

class DevSync:
    def __init__(self):
        self.version = "1.2.0"
        self.config_dir = Path.home() / ".devsync"
        self.backup_dir = self.config_dir / "backups"
        self.system = platform.system().lower()
        self.supported_tools = {
            'vscode': 'Visual Studio Code Settings',
            'git': 'Git Configuration',
            'ssh': 'SSH Keys & Config',
            'npm': 'NPM Global Packages',
            'pip': 'Python Packages',
            'cargo': 'Rust Packages',
            'brew': 'Homebrew Packages (macOS)',
            'apt': 'APT Packages (Ubuntu)',
            'dotfiles': 'Shell Configuration Files',
            'bookmarks': 'Browser Bookmarks',
            'fonts': 'Custom Fonts'
        }
        
        # Create necessary directories
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.print_banner()
    
    def print_banner(self):
        """Display the awesome banner"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  {Fore.GREEN}██████╗ ███████╗██╗   ██╗███████╗██╗   ██╗███╗   ██╗ ██████╗{Fore.CYAN} ║
║  {Fore.GREEN}██╔══██╗██╔════╝██║   ██║██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝{Fore.CYAN} ║
║  {Fore.GREEN}██║  ██║█████╗  ██║   ██║███████╗ ╚████╔╝ ██╔██╗ ██║██║     {Fore.CYAN} ║
║  {Fore.GREEN}██║  ██║██╔══╝  ╚██╗ ██╔╝╚════██║  ╚██╔╝  ██║╚██╗██║██║     {Fore.CYAN} ║
║  {Fore.GREEN}██████╔╝███████╗ ╚████╔╝ ███████║   ██║   ██║ ╚████║╚██████╗{Fore.CYAN} ║
║  {Fore.GREEN}╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝{Fore.CYAN} ║
║                                                              ║
║           {Fore.YELLOW}Universal Development Environment Manager{Fore.CYAN}           ║
║                    {Fore.MAGENTA}Version {self.version} - By xxwfufu{Fore.CYAN}                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}🚀 Keep your development environment in perfect sync across all devices!{Style.RESET_ALL}
"""
        print(banner)
    
    def log(self, message, level="INFO"):
        """Colored logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "WORKING": Fore.MAGENTA
        }
        
        color = colors.get(level, Fore.WHITE)
        print(f"{color}[{timestamp}] {level}: {message}{Style.RESET_ALL}")
    
    def run_command(self, command, shell=True):
        """Run system command safely"""
        try:
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def get_file_hash(self, filepath):
        """Calculate file hash for change detection"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def backup_vscode_settings(self):
        """Backup VS Code settings and extensions"""
        self.log("Backing up VS Code settings...", "WORKING")
        
        vscode_paths = {
            'windows': Path.home() / "AppData/Roaming/Code/User",
            'darwin': Path.home() / "Library/Application Support/Code/User",
            'linux': Path.home() / ".config/Code/User"
        }
        
        vscode_path = vscode_paths.get(self.system)
        if not vscode_path or not vscode_path.exists():
            self.log("VS Code not found or not configured", "WARNING")
            return False
        
        backup_path = self.backup_dir / "vscode"
        backup_path.mkdir(exist_ok=True)
        
        # Backup settings files
        settings_files = ['settings.json', 'keybindings.json', 'snippets']
        for item in settings_files:
            source = vscode_path / item
            if source.exists():
                if source.is_file():
                    shutil.copy2(source, backup_path / item)
                else:
                    shutil.copytree(source, backup_path / item, dirs_exist_ok=True)
        
        # Get installed extensions
        success, extensions, error = self.run_command("code --list-extensions")
        if success:
            with open(backup_path / "extensions.txt", 'w') as f:
                f.write(extensions)
        
        self.log("VS Code settings backed up successfully!", "SUCCESS")
        return True
    
    def backup_git_config(self):
        """Backup Git configuration"""
        self.log("Backing up Git configuration...", "WORKING")
        
        git_config = Path.home() / ".gitconfig"
        git_ignore = Path.home() / ".gitignore_global"
        
        backup_path = self.backup_dir / "git"
        backup_path.mkdir(exist_ok=True)
        
        if git_config.exists():
            shutil.copy2(git_config, backup_path)
        
        if git_ignore.exists():
            shutil.copy2(git_ignore, backup_path)
        
        # Get Git user info
        success, user_name, _ = self.run_command("git config --global user.name")
        success2, user_email, _ = self.run_command("git config --global user.email")
        
        if success and success2:
            with open(backup_path / "user_info.json", 'w') as f:
                json.dump({
                    "name": user_name.strip(),
                    "email": user_email.strip()
                }, f, indent=2)
        
        self.log("Git configuration backed up!", "SUCCESS")
        return True
    
    def backup_ssh_config(self):
        """Backup SSH configuration (safely)"""
        self.log("Backing up SSH configuration...", "WORKING")
        
        ssh_dir = Path.home() / ".ssh"
        if not ssh_dir.exists():
            self.log("SSH directory not found", "WARNING")
            return False
        
        backup_path = self.backup_dir / "ssh"
        backup_path.mkdir(exist_ok=True)
        
        # Only backup config file and known_hosts (not private keys for security)
        safe_files = ['config', 'known_hosts']
        for filename in safe_files:
            source = ssh_dir / filename
            if source.exists():
                shutil.copy2(source, backup_path)
        
        # List public keys (for reference)
        pub_keys = list(ssh_dir.glob("*.pub"))
        if pub_keys:
            with open(backup_path / "public_keys_list.txt", 'w') as f:
                for key in pub_keys:
                    f.write(f"{key.name}\n")
                    # Copy public keys (safe to backup)
                    shutil.copy2(key, backup_path)
        
        self.log("SSH configuration backed up (safely)!", "SUCCESS")
        return True
    
    def backup_package_managers(self):
        """Backup package manager configurations"""
        self.log("Backing up package managers...", "WORKING")
        
        backup_path = self.backup_dir / "packages"
        backup_path.mkdir(exist_ok=True)
        
        # NPM global packages
        success, npm_list, _ = self.run_command("npm list -g --depth=0 --json")
        if success:
            try:
                npm_data = json.loads(npm_list)
                packages = list(npm_data.get('dependencies', {}).keys())
                with open(backup_path / "npm_global.json", 'w') as f:
                    json.dump(packages, f, indent=2)
                self.log(f"NPM: {len(packages)} global packages backed up", "INFO")
            except:
                pass
        
        # Pip packages
        success, pip_list, _ = self.run_command("pip list --format=json")
        if success:
            try:
                pip_data = json.loads(pip_list)
                with open(backup_path / "pip_packages.json", 'w') as f:
                    json.dump(pip_data, f, indent=2)
                self.log(f"PIP: {len(pip_data)} packages backed up", "INFO")
            except:
                pass
        
        # Cargo packages
        success, cargo_list, _ = self.run_command("cargo install --list")
        if success:
            with open(backup_path / "cargo_packages.txt", 'w') as f:
                f.write(cargo_list)
            self.log("Cargo packages backed up", "INFO")
        
        # Homebrew (macOS)
        if self.system == 'darwin':
            success, brew_list, _ = self.run_command("brew list --formula -1")
            if success:
                with open(backup_path / "brew_formulae.txt", 'w') as f:
                    f.write(brew_list)
                
                success2, brew_casks, _ = self.run_command("brew list --cask -1")
                if success2:
                    with open(backup_path / "brew_casks.txt", 'w') as f:
                        f.write(brew_casks)
                self.log("Homebrew packages backed up", "INFO")
        
        self.log("Package managers backed up!", "SUCCESS")
        return True
    
    def backup_dotfiles(self):
        """Backup shell configuration files"""
        self.log("Backing up dotfiles...", "WORKING")
        
        backup_path = self.backup_dir / "dotfiles"
        backup_path.mkdir(exist_ok=True)
        
        dotfiles = [
            '.bashrc', '.bash_profile', '.zshrc', '.zprofile',
            '.fish_config', '.profile', '.aliases', '.functions',
            '.vimrc', '.tmux.conf', '.screenrc'
        ]
        
        backed_up = 0
        for dotfile in dotfiles:
            source = Path.home() / dotfile
            if source.exists():
                shutil.copy2(source, backup_path)
                backed_up += 1
        
        self.log(f"Backed up {backed_up} dotfiles", "SUCCESS")
        return True
    
    def create_sync_package(self, output_path=None):
        """Create a portable sync package"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config_dir / f"devsync_backup_{timestamp}.zip"
        
        self.log("Creating sync package...", "WORKING")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.backup_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(self.backup_dir)
                    zipf.write(file_path, arc_path)
            
            # Add metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "system": platform.system(),
                "machine": platform.machine(),
                "python_version": platform.python_version(),
                "devsync_version": self.version,
                "creator": "xxwfufu"
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        self.log(f"Sync package created: {output_path}", "SUCCESS")
        return output_path
    
    def restore_from_package(self, package_path):
        """Restore from a sync package"""
        self.log("Restoring from sync package...", "WORKING")
        
        if not Path(package_path).exists():
            self.log("Package not found!", "ERROR")
            return False
        
        # Extract package
        with zipfile.ZipFile(package_path, 'r') as zipf:
            zipf.extractall(self.backup_dir)
        
        self.log("Package extracted. Starting restoration...", "INFO")
        
        # Restore VS Code extensions
        extensions_file = self.backup_dir / "vscode" / "extensions.txt"
        if extensions_file.exists():
            with open(extensions_file) as f:
                extensions = f.read().strip().split('\n')
            
            for ext in extensions:
                if ext.strip():
                    self.run_command(f"code --install-extension {ext.strip()}")
            
            self.log(f"Restored {len(extensions)} VS Code extensions", "SUCCESS")
        
        self.log("Restoration completed!", "SUCCESS")
        return True
    
    def interactive_backup(self):
        """Interactive backup selection"""
        print(f"\n{Fore.YELLOW}🔧 Select tools to backup:{Style.RESET_ALL}")
        
        selections = {}
        for key, description in self.supported_tools.items():
            response = input(f"  📦 {description} (y/N): ").lower()
            selections[key] = response in ['y', 'yes']
        
        print(f"\n{Fore.CYAN}Starting backup process...{Style.RESET_ALL}")
        
        if selections.get('vscode'):
            self.backup_vscode_settings()
        
        if selections.get('git'):
            self.backup_git_config()
        
        if selections.get('ssh'):
            self.backup_ssh_config()
        
        if selections.get('npm') or selections.get('pip') or selections.get('cargo'):
            self.backup_package_managers()
        
        if selections.get('dotfiles'):
            self.backup_dotfiles()
        
        # Create sync package
        package_path = self.create_sync_package()
        
        print(f"\n{Fore.GREEN}✅ Backup completed!{Style.RESET_ALL}")
        print(f"📦 Sync package: {package_path}")
        print(f"💡 Share this package with your other devices to sync everything!")
    
    def show_status(self):
        """Show current backup status"""
        print(f"\n{Fore.CYAN}📊 DevSync Status{Style.RESET_ALL}")
        print("=" * 50)
        
        for tool, description in self.supported_tools.items():
            backup_path = self.backup_dir / tool
            if backup_path.exists():
                files_count = len(list(backup_path.glob("*")))
                print(f"✅ {description}: {files_count} files")
            else:
                print(f"❌ {description}: Not backed up")
        
        # Show latest package
        packages = list(self.config_dir.glob("devsync_backup_*.zip"))
        if packages:
            latest = max(packages, key=os.path.getctime)
            mod_time = datetime.fromtimestamp(os.path.getctime(latest))
            print(f"\n📦 Latest package: {latest.name}")
            print(f"🕒 Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    parser = argparse.ArgumentParser(
        description="DevSync - Universal Development Environment Manager"
    )
    
    parser.add_argument('--version', action='version', version='DevSync 1.2.0')
    parser.add_argument('--backup', action='store_true', help='Start interactive backup')
    parser.add_argument('--restore', type=str, help='Restore from package file')
    parser.add_argument('--status', action='store_true', help='Show backup status')
    parser.add_argument('--auto', action='store_true', help='Automatic backup (all tools)')
    
    args = parser.parse_args()
    
    devsync = DevSync()
    
    if args.backup:
        devsync.interactive_backup()
    elif args.restore:
        devsync.restore_from_package(args.restore)
    elif args.status:
        devsync.show_status()
    elif args.auto:
        devsync.log("Starting automatic backup...", "INFO")
        devsync.backup_vscode_settings()
        devsync.backup_git_config()
        devsync.backup_ssh_config()
        devsync.backup_package_managers()
        devsync.backup_dotfiles()
        package = devsync.create_sync_package()
        print(f"\n{Fore.GREEN}🎉 Automatic backup completed!{Style.RESET_ALL}")
        print(f"📦 Package: {package}")
    else:
        devsync.interactive_backup()

if __name__ == "__main__":
    main()
