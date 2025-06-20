# Pattern Report
*Finds what matters - fast.*<br>
*Searches and summarizes recurring text in PDFs.*


When working with large **PDF** documents, it’s hard to find **specific patterns** or details quickly.

**Pattern Report** scans your PDFs for **multiple patterns** at once - like codes, labels, or keywords - and shows you exactly where they appear.

It **reports** each match with its **location** and gives you a clean **page-by-page summary**, making review **faster, easier** and **accurate**.


> Connect with <a href="https://www.linkedin.com/in/swarupselvaraj/" target="_blank">me</a> for similar requirements or enhancements.
---


## How to perform the One-time Setup

1. Install **Scoop**: a command line installer for windows.

    Open a command prompt and paste the below commands

    ```sh
    PowerShell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
    Read-Host "Press any key to close:"
    exit
    exit
    ```


2. Install 7-Zip, Git and UV using scoop

    Open a command prompt and paste the below commands

    ```sh
    powershell
    scoop install 7zip
    scoop install git
    scoop install main/uv
    Read-Host "Press any key to close:"
    exit
    exit
    ```

3. Clone the files

    Open a command prompt and paste the below commands

    ```sh
    powershell
    git clone https://github.com/engineered-in/pattern-report.git "$env:USERPROFILE\Downloads\pattern-report"
    mkdir "$env:USERPROFILE\Downloads\pattern-report\Documents"
    Read-Host "Press any key to close:"
    exit
    exit
    ```

## How to use after performing the One-time Setup

1. Update your search patterns in the `Downloads\pattern-report\config.toml`.

    More help on configuration <a href="https://github.com/engineered-in/pattern-report/blob/main/config.toml" target="_blank">here.</a>

2. Copy your PDF files into the `Downloads\pattern-report\Documents` folder

3. Double click on the `Downloads\pattern-report\launch.bat` file

> It automatically opens the **timestamped report spreadsheet** from `Downloads\pattern-report\Reports` folder
