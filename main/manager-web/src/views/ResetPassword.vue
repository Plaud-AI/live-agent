<template>
  <div class="reset-container">
    <div class="reset-bg">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <div class="reset-card">
      <div class="logo-section">
        <img src="@/assets/xiaozhi-logo.png" alt="Logo" class="logo" />
        <h1 class="brand-title">{{ $t('auth.resetPassword') }}</h1>
      </div>

      <!-- Invalid Token State -->
      <div v-if="!token" class="error-state">
        <div class="error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h2>Invalid Link</h2>
        <p>This password reset link is invalid or has expired.</p>
        <router-link to="/forgot-password" class="action-btn">
          Request New Link
        </router-link>
      </div>

      <!-- Reset Form -->
      <div v-else-if="!isSuccess" class="reset-form">
        <p class="description">
          Enter your new password below.
        </p>

        <div class="form-group">
          <label class="form-label">{{ $t('auth.newPassword') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input 
              v-model="password" 
              :type="showPassword ? 'text' : 'password'" 
              :placeholder="$t('auth.newPasswordPlaceholder')"
              class="form-input"
            />
            <button class="password-toggle" @click="showPassword = !showPassword" type="button">
              <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
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
              v-model="confirmPassword" 
              :type="showPassword ? 'text' : 'password'" 
              :placeholder="$t('auth.confirmPasswordPlaceholder')"
              class="form-input"
              @keyup.enter="submitReset"
            />
          </div>
        </div>

        <button 
          class="submit-btn"
          @click="submitReset"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">{{ $t('auth.resetPassword') }}</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </div>

      <!-- Success State -->
      <div v-else class="success-state">
        <div class="success-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <h2>{{ $t('auth.resetPasswordSuccess') }}</h2>
        <p>Your password has been reset successfully. You can now log in with your new password.</p>
        <router-link to="/login" class="action-btn">
          {{ $t('auth.signIn') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import Api from "@/apis/api";
import { showDanger } from "@/utils";

export default {
  name: "ResetPassword",
  data() {
    return {
      token: "",
      password: "",
      confirmPassword: "",
      showPassword: false,
      isLoading: false,
      isSuccess: false,
    };
  },
  mounted() {
    this.token = this.$route.query.token || "";
  },
  methods: {
    submitReset() {
      if (!this.password) {
        showDanger(this.$t("auth.passwordRequired"));
        return;
      }

      if (this.password.length < 8) {
        showDanger(this.$t("auth.passwordTooShort"));
        return;
      }

      if (this.password !== this.confirmPassword) {
        showDanger(this.$t("auth.passwordMismatch"));
        return;
      }

      this.isLoading = true;

      Api.auth.resetPassword(
        {
          token: this.token,
          new_password: this.password,
        },
        () => {
          this.isLoading = false;
          this.isSuccess = true;
        },
        (err) => {
          this.isLoading = false;
          showDanger(err.data?.message || this.$t("auth.resetPasswordFailed"));
        }
      );
    },
  },
};
</script>

<style lang="scss" scoped>
.reset-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
}

.reset-bg {
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
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #10b981, #059669);
  top: -150px;
  left: -100px;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  bottom: -100px;
  right: -50px;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(20px, -20px) scale(1.05); }
}

.reset-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 40px;
}

.logo-section {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  width: 56px;
  height: 56px;
  margin-bottom: 16px;
}

.brand-title {
  font-size: 24px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}

.description {
  color: #94a3b8;
  font-size: 15px;
  line-height: 1.6;
  text-align: center;
  margin-bottom: 28px;
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
  padding: 14px 44px;
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

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.7;
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
  to { transform: rotate(360deg); }
}

.error-state,
.success-state {
  text-align: center;

  h2 {
    color: #e2e8f0;
    font-size: 24px;
    margin: 20px 0 12px;
  }

  p {
    color: #94a3b8;
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 24px;
  }
}

.error-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto;
  background: rgba(239, 68, 68, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;

  svg {
    width: 32px;
    height: 32px;
  }
}

.success-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto;
  background: rgba(16, 185, 129, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #10b981;

  svg {
    width: 32px;
    height: 32px;
  }
}

.action-btn {
  display: inline-block;
  padding: 14px 32px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
  }
}
</style>


