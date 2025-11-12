package xiaozhi.common.utils;

import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.security.service.CaptchaService;
import xiaozhi.modules.sys.service.SysParamsService;

/**
 * SM2解密和验证码验证工具类
 * 封装了重复的SM2解密、验证码提取和验证逻辑
 */
@Slf4j
public class Sm2DecryptUtil {
    
    /**
     * 验证码长度
     */
    private static final int CAPTCHA_LENGTH = 5;
    
    /**
     * 解密SM2加密内容，提取验证码并验证（支持禁用SM2加密）
     * @param passwordOrEncrypted SM2加密的密码字符串（或明文密码，取决于配置）
     * @param captchaId 验证码ID
     * @param captcha 验证码明文（禁用SM2时需要单独传入）
     * @param captchaService 验证码服务
     * @param sysParamsService 系统参数服务
     * @return 解密后的实际密码
     */
    public static String decryptAndValidateCaptcha(String passwordOrEncrypted, String captchaId, 
                                                 String captcha,
                                                 CaptchaService captchaService, 
                                                 SysParamsService sysParamsService) {
        // 检查是否启用SM2加密
        Boolean enableSm2Encrypt = sysParamsService.getValueObject(
            Constant.SERVER_ENABLE_SM2_ENCRYPT, 
            Boolean.class
        );
        
        // ⭐ 调试日志：查看SM2加密状态
        log.info("============================================================");
        log.info("🔐 SM2加密状态检查");
        log.info("  - 参数名: {}", Constant.SERVER_ENABLE_SM2_ENCRYPT);
        log.info("  - 读取到的值: {}", enableSm2Encrypt);
        log.info("  - 密码长度: {}", passwordOrEncrypted != null ? passwordOrEncrypted.length() : "null");
        log.info("  - 验证码ID: {}", captchaId);
        log.info("  - 验证码: {}", captcha);
        
        // 默认启用SM2（向后兼容）
        if (enableSm2Encrypt == null) {
            log.warn("  ⚠️  SM2参数未配置，默认启用SM2加密（向后兼容）");
            enableSm2Encrypt = true;
        }
        
        log.info("  - 最终决定: {}", enableSm2Encrypt ? "启用SM2加密" : "禁用SM2（明文模式）");
        log.info("============================================================");
        
        String actualPassword;
        String actualCaptcha;
        
        if (enableSm2Encrypt) {
            // ===== SM2加密模式 =====
            // 获取SM2私钥
            String privateKeyStr = sysParamsService.getValue(Constant.SM2_PRIVATE_KEY, true);
            if (StringUtils.isBlank(privateKeyStr)) {
                throw new RenException(ErrorCode.SM2_KEY_NOT_CONFIGURED);
            }
            
            // 使用SM2私钥解密密码
            String decryptedContent;
            try {
                decryptedContent = SM2Utils.decrypt(privateKeyStr, passwordOrEncrypted);
            } catch (Exception e) {
                throw new RenException(ErrorCode.SM2_DECRYPT_ERROR);
            }
            
            // 分离验证码和密码：前5位是验证码，后面是密码
            if (decryptedContent.length() > CAPTCHA_LENGTH) {
                actualCaptcha = decryptedContent.substring(0, CAPTCHA_LENGTH);
                actualPassword = decryptedContent.substring(CAPTCHA_LENGTH);
            } else {
                throw new RenException(ErrorCode.SM2_DECRYPT_ERROR);
            }
        } else {
            // ===== 明文模式（开发环境） =====
            actualPassword = passwordOrEncrypted;
            actualCaptcha = captcha;
        }
        
        // 检查是否禁用验证码验证
        Boolean disableCaptcha = sysParamsService.getValueObject(
            Constant.SERVER_DISABLE_CAPTCHA, 
            Boolean.class
        );
        
        log.info("🔍 验证码验证检查:");
        log.info("  - server.disable_captcha: {}", disableCaptcha);
        log.info("  - captchaId: {}", captchaId);
        log.info("  - actualCaptcha: {}", actualCaptcha);
        
        // 如果禁用验证码或未提供验证码，则跳过验证
        if (disableCaptcha != null && disableCaptcha) {
            log.info("  ✅ 验证码验证已禁用，跳过验证");
        } else if (captchaId != null && !captchaId.isEmpty() && actualCaptcha != null && !actualCaptcha.isEmpty()) {
            log.info("  🔍 开始验证验证码...");
            boolean captchaValid = captchaService.validate(captchaId, actualCaptcha, true);
            if (!captchaValid) {
                log.error("  ❌ 验证码验证失败");
                throw new RenException(ErrorCode.SMS_CAPTCHA_ERROR);
            }
            log.info("  ✅ 验证码验证成功");
        } else {
            log.info("  ⚠️ 未提供验证码，跳过验证（开发模式）");
        }
        
        return actualPassword;
    }
    
    /**
     * 兼容旧版本的方法（保持向后兼容）
     */
    public static String decryptAndValidateCaptcha(String encryptedPassword, String captchaId, 
                                                 CaptchaService captchaService, 
                                                 SysParamsService sysParamsService) {
        return decryptAndValidateCaptcha(encryptedPassword, captchaId, null, 
                                        captchaService, sysParamsService);
    }
}