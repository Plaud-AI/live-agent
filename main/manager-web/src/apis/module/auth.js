/**
 * Authentication API module
 * Supports Email, Google, and Apple authentication
 */
import { getServiceUrl } from '../api'
import RequestService from '../httpRequest'

export default {
    // ==================== Email Authentication ====================
    
    /**
     * Register with email and password
     * @param {Object} data - { email, password, display_name? }
     */
    registerWithEmail(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/email/register`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.registerWithEmail(data, callback, failCallback)
                })
            }).send()
    },

    /**
     * Login with email and password
     * @param {Object} data - { email, password }
     */
    loginWithEmail(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/email/login`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.loginWithEmail(data, callback, failCallback)
                })
            }).send()
    },

    /**
     * Verify email with token
     * @param {Object} data - { token }
     */
    verifyEmail(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/email/verify`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.verifyEmail(data, callback, failCallback)
                })
            }).send()
    },

    /**
     * Resend verification email
     * @param {Object} data - { email }
     */
    resendVerification(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/email/resend-verification`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.resendVerification(data, callback, failCallback)
                })
            }).send()
    },

    /**
     * Request password reset
     * @param {Object} data - { email }
     */
    forgotPassword(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/email/forgot-password`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.forgotPassword(data, callback, failCallback)
                })
            }).send()
    },

    /**
     * Reset password with token
     * @param {Object} data - { token, new_password }
     */
    resetPassword(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/email/reset-password`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.resetPassword(data, callback, failCallback)
                })
            }).send()
    },

    // ==================== Google Authentication ====================

    /**
     * Login with Google ID token
     * @param {Object} data - { id_token }
     */
    loginWithGoogle(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/google/login`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.loginWithGoogle(data, callback, failCallback)
                })
            }).send()
    },

    // ==================== Apple Authentication ====================

    /**
     * Login with Apple ID token
     * @param {Object} data - { id_token, authorization_code?, user_info? }
     */
    loginWithApple(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/apple/login`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.loginWithApple(data, callback, failCallback)
                })
            }).send()
    },

    // ==================== Token Management ====================

    /**
     * Refresh access token
     * @param {Object} data - { refresh_token }
     */
    refreshToken(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/refresh`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                failCallback(err)
            })
            .networkFail(() => {
                RequestService.reAjaxFun(() => {
                    this.refreshToken(data, callback, failCallback)
                })
            }).send()
    },

    /**
     * Logout (revoke refresh token)
     * @param {Object} data - { refresh_token }
     */
    logout(data, callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/logout`)
            .method('POST')
            .data(data)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                if (failCallback) failCallback(err)
            })
            .networkFail(() => {
                // Don't retry logout
                if (failCallback) failCallback({ message: 'Network error' })
            }).send()
    },

    /**
     * Logout from all devices
     */
    logoutAll(callback, failCallback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/auth/logout/all`)
            .method('POST')
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .fail((err) => {
                RequestService.clearRequestTime()
                if (failCallback) failCallback(err)
            })
            .networkFail(() => {
                if (failCallback) failCallback({ message: 'Network error' })
            }).send()
    }
}


