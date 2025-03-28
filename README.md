# CLI for SonarQube scan (using [sonarlint-language-server](https://github.com/SonarSource/sonarlint-language-server))

## Installation

Get java from [OpenJDK](http://openjdk.java.net/) or [unzipping `sonarlint-vscode-<arch>.vsix`](https://github.com/SonarSource/sonarlint-vscode/releases)

Get sonarlint-ls by [compiling from source](https://github.com/SonarSource/sonarlint-language-server) or [unzipping `sonarlint-vscode.vsix`](https://github.com/SonarSource/sonarlint-vscode/releases)

Get sonar-python analyzer by [compiling from source](https://github.com/SonarSource/sonar-python) or [unzipping `sonarlint-vscode.vsix`](https://github.com/SonarSource/sonarlint-vscode/releases)

## Usage

### Get rules

`python scan.py --java $JAVA --sonarlint-ls $SONARLINTLS --analyzer $ANALYZER -- list-rules`

You can have more information [here](https://sonarsource.github.io/rspec/)

### Run the scan

`python scan.py --java $JAVA --sonarlint-ls $SONARLINTLS --analyzer $ANALYZER -- analyze [--rules rule1,rule2] [--disable-rules rule1,rule2] --files *.py`

### Run the scan wihtout any dependencies (autodownload)

`./scan.sh analyze --files *.py`