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
//#define	PAM_SM_PASSWORD

#include <security/pam_modules.h>
#include <security/pam_client.h>
#include <security/_pam_macros.h>

static char password_prompt[] = "Password:";

static sqlite3 * pam_sqlite3_connect(const char *db_path)
{
  D(("CONNECT\n"));
  const char *errtext = NULL;
  sqlite3 *db = NULL;
  int rc;

  D(("DBPATH: %s", db_path));
  rc = sqlite3_open(db_path, &db);
  if( rc != SQLITE_OK)
    {
      D(("Can't open database: %s\n", sqlite3_errmsg(db)));
      exit(0);
    }
  else
    {
      D(("Opened database successfully\n"));
    }
  D(("GOTDB"));
  return db;
}

static int verify_password(const char *user,
                           const char *passwd,
                           const char *db_path)
{
  int res;
  sqlite3 *conn;
  sqlite3_stmt *stmt;
  int rc;
  const char *tail;
  const char *errtext = NULL;
  char *query = "SELECT Password FROM PBox WHERE PBox.PBoxId == ?";


  D(("VERIFY\n"));
  if(!(conn = pam_sqlite3_connect(db_path)))
    return PAM_AUTH_ERR;

  D(("PREPARING QUERY\n"));
  D(("USER = %s\n", user));
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

  D(("QUERY READY %d\n", res));

  rc = PAM_AUTH_ERR;

  if (SQLITE_ROW != sqlite3_step(stmt))
    {
      rc = PAM_USER_UNKNOWN;
    }
  else
    {
      const char *stored_pw = (const char *) sqlite3_column_text(stmt, 0);
      D(("STORED %s\n", stored_pw));
      if(strcmp(passwd, stored_pw) == 0)
        {
          D(("SUCCESS\n"));
          rc = PAM_SUCCESS;
        }
    }

  D(("FINALIZING\n"));
  sqlite3_finalize(stmt);
  sqlite3_close(conn);

  D(("RC: %d\n", rc));
  return rc;
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
  const struct pam_message *msgp;
  struct pam_response *resp;

  const char *user;
  char *password;
  char *storedPwd;
  int pam_err;

  D(("Database path: %s", argv[0]));

  /* identify user */

  if ((pam_err = pam_get_user(pamh, &user, NULL)) != PAM_SUCCESS)
    return (pam_err);

  /* Gets conversation item to grab password */
  pam_err = pam_get_item(pamh, PAM_CONV, &ptr);

  if (pam_err != PAM_SUCCESS)
    return (PAM_SYSTEM_ERR);

  conv = (struct pam_conv *) ptr;

  msg.msg_style = PAM_PROMPT_ECHO_OFF;
  msg.msg = password_prompt;
  msgp = &msg;

  password = NULL;
  resp = NULL;
  /* Call conversation */
  pam_err = (*conv->conv)(1, &msgp, &resp, conv->appdata_ptr);

  if (resp != NULL)
    {
      if (pam_err == PAM_SUCCESS)
        password = resp->resp;
      else
        free(resp->resp);
      free(resp);
    }

  if (pam_err != PAM_SUCCESS)
    return (PAM_AUTH_ERR);

  D(("Got pass: %s", password));
  /* compare passwords */
  if((pam_err = verify_password(user, password, argv[0])) != PAM_SUCCESS)
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

/* /\* */
/*  * Account management */
/*  *\/ */

/* pam_sm_acct_mgmt ( pam_handle_t *pamh, int flags, int argc, */
/*                    const char *argv[] ) */
/* { */
/*   return PAM_SUCCESS; */
/* } */

/* /\* */
/*  * Password management */
/*  *\/ */

/* PAM_EXTERN int */
/* pam_sm_chauthtok ( pam_handle_t *pamh, int flags, int argc, */
/*                    const char *argv[] ) */
/* { */
/*   return (PAM_SERVICE_ERR); */
/* } */

#ifdef PAM_MODULE_ENTRY
PAM_MODULE_ENTRY("pam_sfbx_password");
#endif
