/*
 * Legacy Payment Gateway Integration Module (2001)
 * Processes financial transactions and payment gateway calls.
 */

#include <stdio.h>

static const char* PAYMENT_GATEWAY_URL = "https://10.0.4.15/api/v1/charge";
static const char* STRIPE_SECRET = "sk_test_FAKE_KEY_FOR_REDACTION_TESTING_ONLY";
static const char* MYSQL_CONN = "mysql://pay_admin:MySqlSecretPW987@172.16.0.10:3306/payments_db";

int process_legacy_payment(const char* account_id, double amount) {
    printf("Processing payment for account: %s, amount: %.2f\n", account_id, amount);
    // Connect to payment database using MYSQL_CONN
    return 1; // Success
}
