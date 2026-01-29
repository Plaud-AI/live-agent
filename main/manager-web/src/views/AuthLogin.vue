<template>
  <div class="auth-container">
    <!-- Animated background -->
    <div class="auth-bg">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="auth-card">
      <!-- Logo Section -->
      <div class="logo-section">
        <img src="@/assets/xiaozhi-logo.png" alt="Logo" class="logo" />
        <h1 class="brand-title">Live Agent</h1>
      </div>

      <!-- Tab Navigation -->
      <div class="auth-tabs">
        <button 
          :class="['tab-btn', { active: activeTab === 'login' }]"
          @click="activeTab = 'login'"
        >
          {{ $t('auth.signIn') }}
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'register' }]"
          @click="activeTab = 'register'"
        >
          {{ $t('auth.signUp') }}
        </button>
      </div>

      <!-- Login Form -->
      <div v-if="activeTab === 'login'" class="auth-form">
        <div class="form-group">
          <label class="form-label">{{ $t('auth.email') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            <input 
              v-model="loginForm.email" 
              type="email" 
              :placeholder="$t('auth.emailPlaceholder')"
              class="form-input"
              @keyup.enter="handleEmailLogin"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('auth.password') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input 
              v-model="loginForm.password" 
              :type="showPassword ? 'text' : 'password'" 
              :placeholder="$t('auth.passwordPlaceholder')"
              class="form-input"
              @keyup.enter="handleEmailLogin"
            />
            <button class="password-toggle" @click="showPassword = !showPassword" type="button">
              <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="form-options">
          <router-link to="/forgot-password" class="forgot-link">
            {{ $t('auth.forgotPassword') }}
          </router-link>
        </div>

        <button 
          class="submit-btn"
          @click="handleEmailLogin"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">{{ $t('auth.signIn') }}</span>
          <span v-else class="loading-spinner"></span>
        </button>

        <!-- Divider -->
        <div class="divider">
          <span>{{ $t('auth.orContinueWith') }}</span>
        </div>

        <!-- Social Login Buttons -->
        <div class="social-buttons">
          <button class="social-btn google-btn" @click="handleGoogleLogin" :disabled="isLoading">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Google</span>
          </button>

          <button class="social-btn apple-btn" @click="handleAppleLogin" :disabled="isLoading">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
            </svg>
            <span>Apple</span>
          </button>
        </div>
      </div>

      <!-- Register Form -->
      <div v-else class="auth-form">
        <div class="form-group">
          <label class="form-label">{{ $t('auth.displayName') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <input 
              v-model="registerForm.displayName" 
              type="text" 
              :placeholder="$t('auth.displayNamePlaceholder')"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('auth.email') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            <input 
              v-model="registerForm.email" 
              type="email" 
              :placeholder="$t('auth.emailPlaceholder')"
              class="form-input"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('auth.password') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input 
              v-model="registerForm.password" 
              :type="showPassword ? 'text' : 'password'" 
              :placeholder="$t('auth.passwordPlaceholder')"
              class="form-input"
            />
            <button class="password-toggle" @click="showPassword = !showPassword" type="button">
              <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
            </button>
          </div>
          <p class="password-hint">{{ $t('auth.passwordHint') }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('auth.confirmPassword') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input 
              v-model="registerForm.confirmPassword" 
              :type="showPassword ? 'text' : 'password'" 
              :placeholder="$t('auth.confirmPasswordPlaceholder')"
              class="form-input"
              @keyup.enter="handleEmailRegister"
            />
          </div>
        </div>

        <button 
          class="submit-btn"
          @click="handleEmailRegister"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">{{ $t('auth.createAccount') }}</span>
          <span v-else class="loading-spinner"></span>
        </button>

        <!-- Divider -->
        <div class="divider">
          <span>{{ $t('auth.orContinueWith') }}</span>
        </div>

        <!-- Social Login Buttons -->
        <div class="social-buttons">
          <button class="social-btn google-btn" @click="handleGoogleLogin" :disabled="isLoading">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span>Google</span>
          </button>

          <button class="social-btn apple-btn" @click="handleAppleLogin" :disabled="isLoading">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path fill="currentColor" d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
            </svg>
            <span>Apple</span>
          </button>
        </div>
      </div>

      <!-- Terms -->
      <p class="terms-text">
        {{ $t('auth.agreeToTerms') }}
        <a href="#" class="link">{{ $t('auth.termsOfService') }}</a>
        {{ $t('auth.and') }}
        <a href="#" class="link">{{ $t('auth.privacyPolicy') }}</a>
      </p>
    </div>

    <!-- Language Switcher -->
    <div class="language-switcher">
      <el-dropdown trigger="click" @command="changeLanguage">
        <span class="lang-trigger">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="2" y1="12" x2="22" y2="12"/>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
          </svg>
          {{ currentLanguageText }}
        </span>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item command="zh_CN">简体中文</el-dropdown-item>
          <el-dropdown-item command="zh_TW">繁體中文</el-dropdown-item>
          <el-dropdown-item command="en">English</el-dropdown-item>
          <el-dropdown-item command="de">Deutsch</el-dropdown-item>
          <el-dropdown-item command="vi">Tiếng Việt</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import Api from "@/apis/api";
import { changeLanguage } from "@/i18n";
import { showDanger, showSuccess, goToPage } from "@/utils";

export default {
  name: "AuthLogin",
  data() {
    return {
      activeTab: "login",
      showPassword: false,
      isLoading: false,
      loginForm: {
        email: "",
        password: "",
      },
      registerForm: {
        displayName: "",
        email: "",
        password: "",
        confirmPassword: "",
      },
    };
  },
  computed: {
    currentLanguageText() {
      const lang = this.$i18n.locale;
      const langMap = {
        zh_CN: "简体中文",
        zh_TW: "繁體中文",
        en: "English",
        de: "Deutsch",
        vi: "Tiếng Việt",
      };
      return langMap[lang] || "English";
    },
  },
  mounted() {
    // Check if user is already logged in
    if (this.$store.getters.getToken) {
      goToPage("/home");
    }
    
    // Load Google Sign-In SDK
    this.loadGoogleSDK();
    
    // Load Apple Sign-In SDK
    this.loadAppleSDK();
  },
  methods: {
    // Load Google Sign-In SDK
    loadGoogleSDK() {
      if (document.getElementById('google-signin-sdk')) return;
      
      const script = document.createElement('script');
      script.id = 'google-signin-sdk';
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    },

    // Load Apple Sign-In SDK
    loadAppleSDK() {
      if (document.getElementById('apple-signin-sdk')) return;
      
      const script = document.createElement('script');
      script.id = 'apple-signin-sdk';
      script.src = 'https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js';
      script.async = true;
      document.head.appendChild(script);
    },

    // Change language
    changeLanguage(lang) {
      changeLanguage(lang);
      this.$message.success(this.$t("message.success"));
    },

    // Email login
    async handleEmailLogin() {
      if (!this.loginForm.email) {
        showDanger(this.$t("auth.emailRequired"));
        return;
      }
      if (!this.loginForm.password) {
        showDanger(this.$t("auth.passwordRequired"));
        return;
      }

      this.isLoading = true;

      Api.auth.loginWithEmail(
        this.loginForm,
        ({ data }) => {
          this.isLoading = false;
          this.handleLoginSuccess(data.data);
        },
        (err) => {
          this.isLoading = false;
          showDanger(err.data?.message || this.$t("auth.loginFailed"));
        }
      );
    },

    // Email register
    async handleEmailRegister() {
      if (!this.registerForm.email) {
        showDanger(this.$t("auth.emailRequired"));
        return;
      }
      if (!this.registerForm.password) {
        showDanger(this.$t("auth.passwordRequired"));
        return;
      }
      if (this.registerForm.password.length < 8) {
        showDanger(this.$t("auth.passwordTooShort"));
        return;
      }
      if (this.registerForm.password !== this.registerForm.confirmPassword) {
        showDanger(this.$t("auth.passwordMismatch"));
        return;
      }

      this.isLoading = true;

      Api.auth.registerWithEmail(
        {
          email: this.registerForm.email,
          password: this.registerForm.password,
          display_name: this.registerForm.displayName || undefined,
        },
        ({ data }) => {
          this.isLoading = false;
          showSuccess(this.$t("auth.registrationSuccess"));
          this.activeTab = "login";
          this.loginForm.email = this.registerForm.email;
          // Clear register form
          this.registerForm = {
            displayName: "",
            email: "",
            password: "",
            confirmPassword: "",
          };
        },
        (err) => {
          this.isLoading = false;
          showDanger(err.data?.message || this.$t("auth.registrationFailed"));
        }
      );
    },

    // Google login
    async handleGoogleLogin() {
      if (!window.google) {
        showDanger(this.$t("auth.googleNotLoaded"));
        return;
      }

      this.isLoading = true;

      try {
        // Initialize Google Sign-In
        const client = window.google.accounts.oauth2.initTokenClient({
          client_id: process.env.VUE_APP_GOOGLE_CLIENT_ID,
          scope: 'email profile',
          callback: (response) => {
            if (response.access_token) {
              // Get ID token using the access token
              this.fetchGoogleUserInfo(response.access_token);
            } else {
              this.isLoading = false;
              showDanger(this.$t("auth.googleLoginFailed"));
            }
          },
        });
        
        client.requestAccessToken();
      } catch (error) {
        this.isLoading = false;
        console.error('Google login error:', error);
        showDanger(this.$t("auth.googleLoginFailed"));
      }
    },

    // Fetch Google user info and login
    async fetchGoogleUserInfo(accessToken) {
      try {
        const response = await fetch(
          `https://www.googleapis.com/oauth2/v3/userinfo?access_token=${accessToken}`
        );
        const userInfo = await response.json();
        
        // For simplicity, we'll use access_token directly
        // In production, you should use proper ID token flow
        Api.auth.loginWithGoogle(
          { id_token: accessToken },
          ({ data }) => {
            this.isLoading = false;
            this.handleLoginSuccess(data.data);
          },
          (err) => {
            this.isLoading = false;
            showDanger(err.data?.message || this.$t("auth.googleLoginFailed"));
          }
        );
      } catch (error) {
        this.isLoading = false;
        console.error('Google user info error:', error);
        showDanger(this.$t("auth.googleLoginFailed"));
      }
    },

    // Apple login
    async handleAppleLogin() {
      if (!window.AppleID) {
        showDanger(this.$t("auth.appleNotLoaded"));
        return;
      }

      this.isLoading = true;

      try {
        // Initialize Apple Sign-In
        window.AppleID.auth.init({
          clientId: process.env.VUE_APP_APPLE_CLIENT_ID,
          scope: 'name email',
          redirectURI: window.location.origin + '/auth/apple/callback',
          usePopup: true,
        });

        const response = await window.AppleID.auth.signIn();
        
        Api.auth.loginWithApple(
          {
            id_token: response.authorization.id_token,
            authorization_code: response.authorization.code,
            user_info: response.user,
          },
          ({ data }) => {
            this.isLoading = false;
            this.handleLoginSuccess(data.data);
          },
          (err) => {
            this.isLoading = false;
            showDanger(err.data?.message || this.$t("auth.appleLoginFailed"));
          }
        );
      } catch (error) {
        this.isLoading = false;
        if (error.error !== 'popup_closed_by_user') {
          console.error('Apple login error:', error);
          showDanger(this.$t("auth.appleLoginFailed"));
        }
      }
    },

    // Handle successful login
    handleLoginSuccess(data) {
      // Store tokens
      const tokenData = {
        token: data.access_token,
        refreshToken: data.refresh_token,
        user: data.user,
      };
      this.$store.commit("setToken", JSON.stringify(tokenData));
      
      showSuccess(this.$t("auth.loginSuccess"));
      goToPage("/home");
    },
  },
};
</script>

<style lang="scss" scoped>
// CSS Variables for theming
:root {
  --auth-primary: #6366f1;
  --auth-primary-dark: #4f46e5;
  --auth-secondary: #8b5cf6;
  --auth-bg: #0f0f23;
  --auth-card-bg: rgba(255, 255, 255, 0.03);
  --auth-text: #e2e8f0;
  --auth-text-muted: #94a3b8;
  --auth-border: rgba(255, 255, 255, 0.1);
  --auth-input-bg: rgba(255, 255, 255, 0.05);
}

.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
}

// Animated background
.auth-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 0;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  top: -200px;
  left: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #ec4899, #f43f5e);
  bottom: -150px;
  right: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #06b6d4, #3b82f6);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(30px, -30px) scale(1.05);
  }
  50% {
    transform: translate(-20px, 20px) scale(0.95);
  }
  75% {
    transform: translate(20px, 30px) scale(1.02);
  }
}

// Auth card
.auth-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 40px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

// Logo section
.logo-section {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.3));
}

.brand-title {
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

// Tab navigation
.auth-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 28px;
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover:not(.active) {
    color: #e2e8f0;
  }

  &.active {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
  }
}

// Form styles
.auth-form {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: #64748b;
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: 14px 14px 14px 44px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #e2e8f0;
  font-size: 15px;
  transition: all 0.3s ease;

  &::placeholder {
    color: #64748b;
  }

  &:focus {
    outline: none;
    border-color: #6366f1;
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  }
}

.password-toggle {
  position: absolute;
  right: 14px;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: color 0.2s;

  &:hover {
    color: #94a3b8;
  }

  svg {
    width: 100%;
    height: 100%;
  }
}

.password-hint {
  font-size: 12px;
  color: #64748b;
  margin-top: 6px;
}

.form-options {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 24px;
}

.forgot-link {
  color: #8b5cf6;
  font-size: 13px;
  text-decoration: none;
  transition: color 0.2s;

  &:hover {
    color: #a78bfa;
  }
}

// Submit button
.submit-btn {
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  &:hover::before {
    opacity: 1;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
  }

  &:active {
    transform: translateY(0);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.7;
    transform: none;

    &:hover {
      box-shadow: none;
    }
  }

  span {
    position: relative;
    z-index: 1;
  }
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

// Divider
.divider {
  display: flex;
  align-items: center;
  margin: 28px 0;
  color: #64748b;
  font-size: 13px;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
  }

  span {
    padding: 0 16px;
  }
}

// Social buttons
.social-buttons {
  display: flex;
  gap: 12px;
}

.social-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
    transform: none;
  }
}

.social-icon {
  width: 20px;
  height: 20px;
}

.google-btn:hover {
  border-color: #4285F4;
  box-shadow: 0 4px 15px rgba(66, 133, 244, 0.2);
}

.apple-btn:hover {
  border-color: #fff;
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
}

// Terms text
.terms-text {
  text-align: center;
  font-size: 12px;
  color: #64748b;
  margin-top: 24px;
  line-height: 1.6;
}

.link {
  color: #8b5cf6;
  text-decoration: none;
  transition: color 0.2s;

  &:hover {
    color: #a78bfa;
    text-decoration: underline;
  }
}

// Language switcher
.language-switcher {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
}

.lang-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #e2e8f0;
  }

  svg {
    width: 16px;
    height: 16px;
  }
}

// Responsive
@media (max-width: 480px) {
  .auth-card {
    padding: 28px 20px;
    border-radius: 20px;
  }

  .social-buttons {
    flex-direction: column;
  }

  .logo {
    width: 48px;
    height: 48px;
  }

  .brand-title {
    font-size: 24px;
  }
}
</style>


