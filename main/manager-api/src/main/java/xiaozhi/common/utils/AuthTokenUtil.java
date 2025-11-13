package xiaozhi.common.utils;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;

import javax.crypto.Cipher;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

/**
 * 认证 Token 工具类
 * 与 Python 的 core/utils/auth.py 中的 AuthToken 类保持一致
 * 用于生成和验证包含 device_id 的 JWT token
 */
@Slf4j
public class AuthTokenUtil {
    
    private static final String FIXED_SALT = "fixed_salt_placeholder"; // 与 Python 保持一致
    private static final int ITERATIONS = 100000;
    private static final int GCM_IV_LENGTH = 12;
    private static final int GCM_TAG_LENGTH = 16;
    
    private final byte[] encryptionKey;
    private final byte[] secretKeyBytes;
    private final ObjectMapper objectMapper;
    
    /**
     * 构造函数
     * @param secretKey 密钥字符串（对应 Python 的 auth_key）
     */
    public AuthTokenUtil(String secretKey) {
        this.secretKeyBytes = secretKey.getBytes(StandardCharsets.UTF_8);
        this.encryptionKey = deriveKey(32); // 32 bytes for AES-256
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * 派生固定长度的密钥（与 Python 的 _derive_key 一致）
     */
    private byte[] deriveKey(int length) {
        try {
            PBEKeySpec spec = new PBEKeySpec(
                new String(secretKeyBytes, StandardCharsets.UTF_8).toCharArray(),
                FIXED_SALT.getBytes(StandardCharsets.UTF_8),
                ITERATIONS,
                length * 8 // bits
            );
            SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            return factory.generateSecret(spec).getEncoded();
        } catch (Exception e) {
            throw new RuntimeException("密钥派生失败", e);
        }
    }
    
    /**
     * 使用 AES-GCM 加密 payload（与 Python 的 _encrypt_payload 一致）
     */
    private String encryptPayload(Map<String, Object> payload) {
        try {
            // 将 payload 转换为 JSON 字符串
            String payloadJson = objectMapper.writeValueAsString(payload);
            byte[] plaintext = payloadJson.getBytes(StandardCharsets.UTF_8);
            
            // 生成随机 IV
            byte[] iv = new byte[GCM_IV_LENGTH];
            new SecureRandom().nextBytes(iv);
            
            // 创建加密器
            SecretKeySpec keySpec = new SecretKeySpec(encryptionKey, "AES");
            GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, iv);
            
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, keySpec, gcmSpec);
            
            // 加密（包含自动生成的 tag）
            byte[] ciphertext = cipher.doFinal(plaintext);
            
            // 组合: IV + 密文（已包含 tag）
            ByteBuffer byteBuffer = ByteBuffer.allocate(iv.length + ciphertext.length);
            byteBuffer.put(iv);
            byteBuffer.put(ciphertext);
            
            // Base64 URL-safe 编码
            return Base64.getUrlEncoder().withoutPadding().encodeToString(byteBuffer.array());
        } catch (Exception e) {
            log.error("加密 payload 失败", e);
            throw new RuntimeException("加密失败", e);
        }
    }
    
    /**
     * 使用 AES-GCM 解密 payload（与 Python 的 _decrypt_payload 一致）
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> decryptPayload(String encryptedData) {
        try {
            // Base64 URL-safe 解码
            byte[] data = Base64.getUrlDecoder().decode(encryptedData);
            
            // 拆分组件
            ByteBuffer byteBuffer = ByteBuffer.wrap(data);
            byte[] iv = new byte[GCM_IV_LENGTH];
            byteBuffer.get(iv);
            
            byte[] ciphertext = new byte[byteBuffer.remaining()];
            byteBuffer.get(ciphertext);
            
            // 创建解密器
            SecretKeySpec keySpec = new SecretKeySpec(encryptionKey, "AES");
            GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, iv);
            
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, keySpec, gcmSpec);
            
            // 解密
            byte[] plaintext = cipher.doFinal(ciphertext);
            String payloadJson = new String(plaintext, StandardCharsets.UTF_8);
            
            // 转换为 Map
            return objectMapper.readValue(payloadJson, Map.class);
        } catch (Exception e) {
            log.error("解密 payload 失败", e);
            throw new RuntimeException("解密失败", e);
        }
    }
    
    /**
     * 生成 JWT token（与 Python 的 generate_token 一致）
     * @param deviceId 设备ID
     * @return JWT token 字符串
     */
    public String generateToken(String deviceId) {
        try {
            // 设置过期时间为 1 小时后
            Instant expireTime = Instant.now().plus(1, ChronoUnit.HOURS);
            
            // 创建原始 payload
            Map<String, Object> payload = new HashMap<>();
            payload.put("device_id", deviceId);
            payload.put("exp", expireTime.getEpochSecond());
            
            // 加密整个 payload
            String encryptedPayload = encryptPayload(payload);
            
            // 创建外层 payload
            Map<String, Object> outerPayload = new HashMap<>();
            outerPayload.put("data", encryptedPayload);
            
            // 使用 JWT 进行编码
            Algorithm algorithm = Algorithm.HMAC256(secretKeyBytes);
            String token = JWT.create()
                .withPayload(outerPayload)
                .sign(algorithm);
            
            log.info("生成 device JWT token 成功: deviceId={}", deviceId);
            return token;
            
        } catch (Exception e) {
            log.error("生成 token 失败: deviceId={}", deviceId, e);
            throw new RuntimeException("生成 token 失败", e);
        }
    }
    
    /**
     * 验证 token（与 Python 的 verify_token 一致）
     * @param token JWT token 字符串
     * @return 设备ID，验证失败返回 null
     */
    public String verifyToken(String token) {
        try {
            // 先验证外层 JWT（签名）
            Algorithm algorithm = Algorithm.HMAC256(secretKeyBytes);
            DecodedJWT jwt = JWT.require(algorithm).build().verify(token);
            
            // 获取加密的内层 payload
            String encryptedData = jwt.getClaim("data").asString();
            if (encryptedData == null) {
                log.warn("Token 缺少 data 字段");
                return null;
            }
            
            // 解密内层 payload
            Map<String, Object> innerPayload = decryptPayload(encryptedData);
            
            // 检查过期时间（双重验证）
            Number expNumber = (Number) innerPayload.get("exp");
            if (expNumber == null) {
                log.warn("Token payload 缺少 exp 字段");
                return null;
            }
            
            long exp = expNumber.longValue();
            if (exp < Instant.now().getEpochSecond()) {
                log.warn("Token 已过期: exp={}", exp);
                return null;
            }
            
            String deviceId = (String) innerPayload.get("device_id");
            log.debug("Token 验证成功: deviceId={}", deviceId);
            return deviceId;
            
        } catch (Exception e) {
            log.warn("Token 验证失败: {}", e.getMessage());
            return null;
        }
    }
}

