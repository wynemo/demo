
#ifdef _WIN32

#define WIN_EXPORT __declspec(dllexport)

#else

#define WIN_EXPORT
#endif



WIN_EXPORT int daslicSignOnline(char *code, char *email, char *post_back, char *proxy);

WIN_EXPORT int daslicSignOffline(char *code, char *email, char **result, int *rlen, char *post_back);

WIN_EXPORT int daslicSignManual(char *email, char **result, int *rlen, char *post_back);

WIN_EXPORT int daslicInitLog(char *path, int level);

WIN_EXPORT int daslicInitWorkDir(char *path, char *product_name, char *product_model);

WIN_EXPORT int daslicGetSn(char **result);

WIN_EXPORT int daslicVerifyLicense(char *lic_path, char **result, int *len, int strict);

WIN_EXPORT int daslicVerifyLicenseDef(char **result, int *rlen, int strict);

//增加一个只校验证书合法的功能

WIN_EXPORT void daslicFree(void *data);