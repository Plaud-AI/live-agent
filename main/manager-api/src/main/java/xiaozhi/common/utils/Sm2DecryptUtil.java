package xiaozhi.common.utils;

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
        
        // 默认启用SM2（向后兼容）
        if (enableSm2Encrypt == null) {
            enableSm2Encrypt = true;
        }
        
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
        
        // 验证验证码是否正确（如果提供了验证码）
        if (captchaId != null && !captchaId.isEmpty() && actualCaptcha != null && !actualCaptcha.isEmpty()) {
            boolean captchaValid = captchaService.validate(captchaId, actualCaptcha, true);
            if (!captchaValid) {
                throw new RenException(ErrorCode.SMS_CAPTCHA_ERROR);
            }
        }
        // 否则跳过验证码验证（开发环境）
        
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