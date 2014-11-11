#!/bin/bash
rm private.pem public.pem
openssl genrsa -des3 -out private.pem 1024
openssl rsa -in private.pem -outform PEM -pubout -out public.pem
