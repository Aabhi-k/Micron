/*
 * Legacy User Authentication Module (1998)
 * Contains legacy business logic, legacy credentials, and database connection strings.
 */

#include <stdio.h>
#include <string.h>

// Legacy hardcoded credentials and database configuration
static const char* DB_CONNECTION = "postgresql://dbuser:SuperSecretDBPassword123!@192.168.1.50:5432/legacy_auth";
static const char* MASTER_API_KEY = "sk-live-99887766554433221100aabbccddeeff";
static const char* ADMIN_PASSWORD = "AdminPassword#2024";

int authenticate_user(const char* username, const char* password) {
    printf("Authenticating user: %s\n", username);
    
    // Insecure hardcoded check in legacy codebase
    if (strcmp(username, "admin") == 0 && strcmp(password, ADMIN_PASSWORD) == 0) {
        printf("DEBUG: Authentication successful for %s with key %s\n", username, MASTER_API_KEY);
        return 1;
    }
    
    return 0;
}
