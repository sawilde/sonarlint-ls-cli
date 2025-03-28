if [ ! -e ~/.sonarlint-ls ]; then
    mkdir -p ~/.sonarlint-ls
    pushd ~/.sonarlint-ls > /dev/null
    curl -L https://github.com/SonarSource/sonarlint-vscode/releases/download/4.18.0%2B77392/sonarlint-vscode-4.18.0.vsix > sonar.zip
    unzip -q sonar.zip -d tmp
    rm sonar.zip
    mv tmp/extension/analyzers tmp/extension/server .
    rm -rf tmp
    popd > /dev/null
fi

if [ ! -e ~/.sonarlint-ls/venv ]; then
    python3 -m venv ~/.sonarlint-ls/venv
    ~/.sonarlint-ls/venv/bin/pip install -r requirements.txt
fi
~/.sonarlint-ls/venv/bin/python scan.py --sonarlint-ls ~/.sonarlint-ls/server/*.jar --analyzers ~/.sonarlint-ls/analyzers/*.jar -- $*