<template>
  <div class="forgot-container">
    <div class="forgot-bg">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <div class="forgot-card">
      <div class="logo-section">
        <img src="@/assets/xiaozhi-logo.png" alt="Logo" class="logo" />
        <h1 class="brand-title">{{ $t('auth.resetPassword') }}</h1>
      </div>

      <!-- Request Form -->
      <div v-if="!isSubmitted" class="forgot-form">
        <p class="description">
          Enter your email address and we'll send you a link to reset your password.
        </p>

        <div class="form-group">
          <label class="form-label">{{ $t('auth.email') }}</label>
          <div class="input-wrapper">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
            <input 
              v-model="email" 
              type="email" 
              :placeholder="$t('auth.emailPlaceholder')"
              class="form-input"
              @keyup.enter="submitRequest"
            />
          </div>
        </div>

        <button 
          class="submit-btn"
          @click="submitRequest"
          :disabled="isLoading"
        >
          <span v-if="!isLoading">{{ $t('auth.sendResetLink') }}</span>
          <span v-else class="loading-spinner"></span>
        </button>

        <router-link to="/login" class="back-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          {{ $t('auth.backToLogin') }}
        </router-link>
      </div>

      <!-- Success State -->
      <div v-else class="success-state">
        <div class="success-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <h2>Check Your Email</h2>
        <p>We've sent a password reset link to <strong>{{ email }}</strong></p>
        <p class="hint">Didn't receive the email? Check your spam folder or try again.</p>
        
        <button class="submit-btn secondary" @click="isSubmitted = false">
          Try Another Email
        </button>
        
        <router-link to="/login" class="back-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          {{ $t('auth.backToLogin') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import Api from "@/apis/api";
import { showDanger } from "@/utils";

export default {
  name: "ForgotPassword",
  data() {
    return {
      email: "",
      isLoading: false,
      isSubmitted: false,
    };
  },
  methods: {
    submitRequest() {
      if (!this.email) {
        showDanger(this.$t("auth.emailRequired"));
        return;
      }

      // Simple email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        showDanger("Please enter a valid email address");
        return;
      }

      this.isLoading = true;

      Api.auth.forgotPassword(
        { email: this.email },
        () => {
          this.isLoading = false;
          this.isSubmitted = true;
        },
        () => {
          // Even on error, show success to prevent email enumeration
          this.isLoading = false;
          this.isSubmitted = true;
        }
      );
    },
  },
};
</script>

<style lang="scss" scoped>
.forgot-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
}

.forgot-bg {
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
  background: linear-gradient(135deg, #f59e0b, #d97706);
  top: -150px;
  right: -100px;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  bottom: -100px;
  left: -50px;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-20px, 20px) scale(1.05); }
}

.forgot-card {
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
  margin-bottom: 24px;
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
  margin-bottom: 20px;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }

  &.secondary {
    background: rgba(255, 255, 255, 0.1);
    margin-bottom: 16px;
    
    &:hover:not(:disabled) {
      background: rgba(255, 255, 255, 0.15);
      box-shadow: none;
    }
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

.back-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #8b5cf6;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;

  svg {
    width: 18px;
    height: 18px;
  }

  &:hover {
    color: #a78bfa;
  }
}

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
    margin-bottom: 8px;

    strong {
      color: #e2e8f0;
    }
  }

  .hint {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 24px;
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
</style>


