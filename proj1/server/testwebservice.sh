#!/bin/bash
printf "\nResource: pboxes, Method: list\n"
curl -X GET 'http://localhost:8000/session/?method=getkey' 
printf "\nResource: pboxes, Method: list\n"
curl -X GET 'http://localhost:8000/pboxes/?method=list'
printf "\n\nResource: pboxes, Method: get_mdata\n"
curl -X GET 'http://localhost:8000/pboxes/?method=get_mdata&ccid=123456789'
curl -X GET 'http://localhost:8000/pboxes/?method=get_mdata&ccid=987654321'
printf "\n\nResource: pboxes, Method: register\n"
curl -X PUT 'http://localhost:8000/pboxes/?method=register&ccid=234567890&name=Joao&pubkey=aaa'
printf "\n\nResource: pboxes, Method2: register\n"
curl -X PUT 'http://localhost:8000/pboxes/?method=register&ccid=234567890&name=Joao&pubkey=aaa'
printf "\n"
printf "\n\nResource: pboxes, Method: list\n"
curl -X GET 'http://localhost:8000/pboxes/?method=list'
printf "\n\nResource: files, Method: list\n"
curl -X GET 'http://localhost:8000/files/?method=list&pboxid=1'
printf "\n"
./populate_db.sh
printf "\n"
