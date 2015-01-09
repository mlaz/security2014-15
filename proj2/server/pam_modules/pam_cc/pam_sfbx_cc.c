/*
 * Partially based on PAM_PTEIDCC.c https://code.ua.pt/git/ccpam
 * Usage: auth sufficient pam_sfbx_cc.so [path to SafeBox database]
 */

#define PAM_DEBUG

#include <sys/param.h>

#include <pwd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sqlite3.h>
#include <crypt.h>

#include <syslog.h>

#define PAM_SM_AUTH
//#define PAM_SM_ACCOUNT
//#define PAM_SM_PASSWORD

#include <security/pam_modules.h>
#include <security/pam_client.h>
#include <security/_pam_macros.h>

#include <openssl/rsa.h>
#include <openssl/sha.h>
#include <openssl/x509.h>
#include <openssl/pem.h>

#include <openssl/bio.h>
#include <openssl/evp.h>

static char original_prompt[] = "Original:";
static char sign_prompt[] = "Signature:";

/* Base64 decoding utility based on https://gist.github.com/barrysteyn/4409525 */
static int calcDecodeLength(const char* b64input) { //Calculates the length of a decoded base64 string
  int len = strlen(b64input);
  int padding = 0;

  if (b64input[len-1] == '=' && b64input[len-2] == '=') //last two chars are =
    padding = 2;
  else if (b64input[len-1] == '=') //last char is =
    padding = 1;

  return (int)len*0.75 - padding;
}

static int Base64Decode(char* b64message, char** buffer) { //Decodes a base64 encoded string
  BIO *bio, *b64;
  int decodeLen = calcDecodeLength(b64message),
      len = 0;
  *buffer = (char*)malloc(decodeLen+1);
  FILE* stream = fmemopen(b64message, strlen(b64message), "r");

  b64 = BIO_new(BIO_f_base64());
  bio = BIO_new_fp(stream, BIO_NOCLOSE);
  bio = BIO_push(b64, bio);
  BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL); //Do not use newlines to flush buffer
  len = BIO_read(bio, *buffer, strlen(b64message));
    //Can test here if len == decodeLen - if not, then return an error
  (*buffer)[len] = '\0';

  BIO_free_all(bio);
  fclose(stream);

  return decodeLen; //success
}

static sqlite3 * pam_sqlite3_connect(const char *db_path)
{
  //D(("CONNECT\n"));
  const char *errtext = NULL;
  sqlite3 *sdb = NULL;
  int rc;

  //D(("DBPATH: %s", db_path));
  rc = sqlite3_open(db_path, &sdb);
  if( rc != SQLITE_OK)
    {
      D(("Can't open database: %s\n", sqlite3_errmsg(sdb)));
      exit(0);
    }
  else
    {
      //D(("Opened database successfully\n"));
    }
  //D(("GOTDB"));
  return sdb;
}

int pass_cb(char *buf, int size, int rwflag, void *u)
{
  return 0;
}

static int verify_signature(const char *user,
                            char *original64,
                            char *sign64,
                            const char *db_path)
{
  //for database interaction
  int res;
  sqlite3 *conn;
  sqlite3_stmt *stmt;
  const char *tail;
  const char *errtext = NULL;
  char *query = "SELECT UserCCKey FROM PBox WHERE PBox.PBoxId == ?";

  //for signature validation
  int ret;
  char *original;
  int ori_len;
  char *sign;
  int sig_len;
  SHA_CTX ctx;
  unsigned char digest[20];
  BIO *bufio;
  RSA *rsakey = RSA_new();
  int key;

  D(("VERIFY\n"));
  if(!(conn = pam_sqlite3_connect(db_path)))
    return PAM_AUTH_ERR;

  // getting cckey
  //D(("PREPARING QUERY\n"));
  //D(("USER = %s\n", user));
  res = sqlite3_prepare_v2(conn, query, strlen(query)+1, &stmt, &tail);
  if (res != SQLITE_OK)
    {
      return PAM_AUTH_ERR;
    }

  if (sqlite3_bind_text(stmt, 1, user, strlen(user), SQLITE_STATIC) != SQLITE_OK)
   {
    printf("\nCould not bind text.\n");
    return  PAM_AUTH_ERR;
  }

  //D(("QUERY READY %d\n", res));

  ret = PAM_AUTH_ERR;

  if (SQLITE_ROW != sqlite3_step(stmt))
    {
      ret = PAM_USER_UNKNOWN;
    }
  else
    {
      // Verifying signature
      char *key_pem = (char *) sqlite3_column_text(stmt, 0);
      //D(("KEY: %s\n", key_pem));

      bufio = BIO_new_mem_buf(key_pem, -1);

      rsakey = PEM_read_bio_RSA_PUBKEY(bufio, &rsakey, NULL, NULL);
      //D(("KEY: %d\n", key));

      int avail = RSA_size((const RSA*) rsakey);
      //D(("KEY AVAILABLE: %d\n", avail));
      sig_len = Base64Decode(sign64, &sign);
      //D(("Decoded Signature: %s\n", sign));

      ori_len = Base64Decode(original64, &original);
      //D(("Decoded Challange: %s\n", original));

      SHA1_Init ( &ctx );
      SHA1_Update ( &ctx, original, ori_len );
      SHA1_Final ( digest, &ctx );

      //D(("DIGEST SZ: %d\n", sizeof(digest)));
      //D(("SIGN SZ: %d\n", sig_len));
      if ( RSA_verify(NID_sha1, digest, sizeof(digest), sign, sig_len, rsakey) == 1 )
        {
          D(("SUCCESS\n"));
          ret = PAM_SUCCESS;
        }
    }

  //D(("FINALIZING DB\n"));
  sqlite3_finalize(stmt);
  sqlite3_close(conn);

  //D(("RET: %d\n", ret));
  return ret;
}

PAM_EXTERN int
pam_sm_authenticate(pam_handle_t *pamh,
                    int flags,
                    int argc,
                    const char *argv[])
{
  const void *ptr;
  struct pam_conv *conv;
  struct pam_message msg;
  struct pam_message msg1;
  const struct pam_message *msgp;
  struct pam_response *resp;

  const char *user;
  char *original64;
  char *sign64;

  int pam_err;

  D(("Database path: %s", argv[0]));

  /* identify user */

  if ((pam_err = pam_get_user(pamh, &user, NULL)) != PAM_SUCCESS)
    return (pam_err);

  D(("Got User: %s", user));
  /* Setting up pam conversation function */
  pam_err = pam_get_item(pamh, PAM_CONV, &ptr);

  if (pam_err != PAM_SUCCESS)
    return (PAM_SYSTEM_ERR);

  conv = (struct pam_conv *) ptr;

  /* Getting the original data */
  msg.msg_style = PAM_PROMPT_ECHO_OFF;
  msg.msg = original_prompt;
  msgp = &msg;

  original64 = NULL;
  resp = NULL;
  pam_err = (*conv->conv)(1, &msgp, &resp, conv->appdata_ptr);

  if (resp != NULL)
    {
      if (pam_err == PAM_SUCCESS)
        original64 = resp->resp;
      else
        free(resp->resp);
      free(resp);
    }

  if (pam_err != PAM_SUCCESS)
    return (PAM_AUTH_ERR);

  //D(("Got Challange: %s", original64));

  /* Getting the signed data */
  msg1.msg_style = PAM_PROMPT_ECHO_OFF;
  msg1.msg = sign_prompt;
  msgp = &msg1;

  sign64 = NULL;
  resp = NULL;
  pam_err = (*conv->conv)(1, &msgp, &resp, conv->appdata_ptr);

  if (resp != NULL)
    {
      if (pam_err == PAM_SUCCESS)
        sign64 = resp->resp;
      else
        free(resp->resp);
      free(resp);
    }

  if (pam_err != PAM_SUCCESS)
    return (PAM_AUTH_ERR);

  //D(("Got Signature: %s", sign64));

  /* verify signature */
  if((pam_err = verify_signature(user, original64, sign64, argv[0])) != PAM_SUCCESS)
    {
      D(("ERROR!\n"));
      return pam_err;
    }

  return PAM_SUCCESS;
}

PAM_EXTERN int
pam_sm_setcred ( pam_handle_t *pamh, int flags, int argc,
                 const char *argv[] )
{
  return PAM_SUCCESS;
}

#ifdef PAM_MODULE_ENTRY
PAM_MODULE_ENTRY("pam_sfbx_cc");
#endif
