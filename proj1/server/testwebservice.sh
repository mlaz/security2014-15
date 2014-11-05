#!/bin/bash
printf "\nResource: pboxes, Mehtod: list\n"
curl -X GET 'http://localhost:8000/pboxes/?method=list'
printf "\n\nResource: pboxes, Mehtod: get_mdata\n"
curl -X GET 'http://localhost:8000/pboxes/?method=get_mdata&ccid=123456789'
curl -X GET 'http://localhost:8000/pboxes/?method=get_mdata&ccid=987654321'
printf "\n\nResource: pboxes, Mehtod: register\n"
curl -X PUT 'http://localhost:8000/pboxes/?method=register&ccid=234567890&name=Joao&pubkey=aaa'
printf "\n"
curl -X GET 'http://localhost:8000/pboxes/?method=list'
printf "\n\nResource: files, Mehtod: list\n"
curl -X GET 'http://localhost:8000/files/?method=list&pboxid=1'
printf "\n"
./populate_db.sh
printf "\n"
