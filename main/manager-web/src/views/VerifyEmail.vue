<template>
  <div class="verify-container">
    <div class="verify-bg">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <div class="verify-card">
      <div class="logo-section">
        <img src="@/assets/xiaozhi-logo.png" alt="Logo" class="logo" />
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="status-content">
        <div class="spinner"></div>
        <h2>{{ $t('auth.verifyEmail') }}</h2>
        <p>{{ $t('message.processing') }}...</p>
      </div>

      <!-- Success State -->
      <div v-else-if="isSuccess" class="status-content success">
        <div class="status-icon success-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <h2>{{ $t('auth.verifyEmailSuccess') }}</h2>
        <p>{{ message }}</p>
        <button class="action-btn" @click="goToLogin">
          {{ $t('auth.signIn') }}
        </button>
      </div>

      <!-- Error State -->
      <div v-else class="status-content error">
        <div class="status-icon error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h2>{{ $t('auth.verifyEmailFailed') }}</h2>
        <p>{{ errorMessage }}</p>
        <div class="action-buttons">
          <button class="action-btn secondary" @click="resendVerification">
            {{ $t('auth.resendVerification') }}
          </button>
          <button class="action-btn" @click="goToLogin">
            {{ $t('auth.backToLogin') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Api from "@/apis/api";
import { goToPage } from "@/utils";

export default {
  name: "VerifyEmail",
  data() {
    return {
      isLoading: true,
      isSuccess: false,
      message: "",
      errorMessage: "",
      email: "",
    };
  },
  mounted() {
    this.verifyEmail();
  },
  methods: {
    async verifyEmail() {
      const token = this.$route.query.token;
      
      if (!token) {
        this.isLoading = false;
        this.errorMessage = "Invalid verification link";
        return;
      }

      Api.auth.verifyEmail(
        { token },
        ({ data }) => {
          this.isLoading = false;
          this.isSuccess = true;
          this.message = data.data?.message || "Your email has been verified successfully!";
          this.email = data.data?.email || "";
        },
        (err) => {
          this.isLoading = false;
          this.isSuccess = false;
          this.errorMessage = err.data?.message || "Verification failed. The link may be expired or invalid.";
        }
      );
    },

    async resendVerification() {
      // If we have the email, try to resend
      if (this.email) {
        Api.auth.resendVerification(
          { email: this.email },
          () => {
            this.$message.success(this.$t("auth.resendVerificationSuccess"));
          },
          (err) => {
            this.$message.error(err.data?.message || "Failed to resend verification email");
          }
        );
      } else {
        // Redirect to login with a message
        goToPage("/login");
      }
    },

    goToLogin() {
      goToPage("/login");
    },
  },
};
</script>

<style lang="scss" scoped>
.verify-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
}

.verify-bg {
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

.verify-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: rgba(15, 15, 35, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 40px;
  text-align: center;
}

.logo-section {
  margin-bottom: 32px;
}

.logo {
  width: 64px;
  height: 64px;
}

.status-content {
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

.spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;

  svg {
    width: 32px;
    height: 32px;
  }
}

.success-icon {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.error-icon {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
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

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
  }

  &.secondary {
    background: rgba(255, 255, 255, 0.1);
    
    &:hover {
      background: rgba(255, 255, 255, 0.15);
      box-shadow: none;
    }
  }
}
</style>


