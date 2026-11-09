# Rebuild the README demo: vhs assets/demo.tape (from the repository root)
Output assets/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1200
Set Height 520
Set Padding 24
Set TypingSpeed 35ms
Set Theme { "name": "verbump", "background": "#0D1117", "foreground": "#E6EDF3", "cursor": "#58A6FF", "selection": "#30363D", "black": "#161B22", "brightBlack": "#9198A1", "red": "#F85149", "brightRed": "#FF7B72", "green": "#3FB950", "brightGreen": "#56D364", "yellow": "#D29922", "brightYellow": "#E3B341", "blue": "#58A6FF", "brightBlue": "#79C0FF", "magenta": "#D2A8FF", "brightMagenta": "#E2C5FF", "cyan": "#76E3EA", "brightCyan": "#B3F0FF", "white": "#E6EDF3", "brightWhite": "#FFFFFF" }

Hide
Type `export PS1='$ ' PYTHONPATH=$PWD/src && verbump() { python3 -m verbump "$@"; } && cd $(python3 -m verbump demo --setup-only) && clear`
Enter
Sleep 1s
Show

Type "# two packages, both released: api (Python) and web (Node)"
Sleep 200ms
Enter
Type "verbump status"
Sleep 300ms
Enter
Sleep 2s

Type "# a PR from feat/checkout changed apps/web and added a changelog note"
Sleep 200ms
Enter
Type "git log --oneline --stat -1"
Sleep 300ms
Enter
Sleep 2.5s

Type "verbump apply --branch feat/checkout"
Sleep 300ms
Enter
Sleep 2.5s

Type "git diff apps/web/package.json | tail -3"
Sleep 300ms
Enter
Sleep 2s

Type "# the release notes, for the GitHub release"
Sleep 200ms
Enter
Type "verbump notes web"
Sleep 300ms
Enter
Sleep 4s
