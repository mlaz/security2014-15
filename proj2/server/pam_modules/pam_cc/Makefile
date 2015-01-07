CFLAGS = -g
PAM_INCLUDE_FILES = $(foreach f, pam_modules.h pam_client.h _pam_macros.h, /usr/include/security/$(f))

all: pam_sfbx_cc.so

pam_sfbx_cc.so: pam_sfbx_cc.o
	ld -o $@ -shared $^ -L /usr/local/lib -lsqlite3 -lpam -lssl -lcrypto

pam_sfbx_cc.o: pam_sfbx_cc.c
	@for f in $(PAM_INCLUDE_FILES); do \
		if test ! -f $$f; then \
			echo "install libpam0g-dev with apt-get or with a similar tool"; \
			exit 1; \
		fi; \
	done; \
	echo $(CC) -o $@ -c -fPIC -fno-stack-protector $*.c $(CFLAGS); \
	$(CC) -o $@ -c -fPIC -fno-stack-protector $*.c $(CFLAGS)


install:
	strip pam_sfbx_cc.so
	cp pam_sfbx_cc.so /lib/security

clean:
	rm *.o pam_sfbx_cc.so
