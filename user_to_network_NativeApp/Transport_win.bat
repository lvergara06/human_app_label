@echo off
:: Options
:: -s CreateUrl , this option lets the extension send the data to the specified CreateUrl. i.e. -s "https://prototypeapi2022.azurewebsites.net/api/Connection/Create" 
:: -E All , this option lets the extension send and extended set of data. "All" means all request headers and response headers. i.e. -E All
:: -o Path, this option lets you pass a list of popup options to the extension for the prompt. i.e. -o "C:/Users/lvergararodr/source/repos/webextensions-examples/Prototype/app/options.txt"
:: python -u C:\Users\lvergararodr\source\repos\webextensions-examples\Prototype\app\Transport.py -s "https://prototypeapi2022.azurewebsites.net/api/Connection/Create" -E All

python -u C:\Users\lvergararodr\source\repos\webextensions-examples\Prototype\app\Transport.py -o "C:/Users/lvergararodr/source/repos/webextensions-examples/Prototype/app/options.txt"
