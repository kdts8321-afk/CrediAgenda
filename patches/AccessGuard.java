package mx.crediagenda.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

final class AccessGuard {
    static final String PIN = "pin";
    static final String PATTERN = "pattern";
    private static final String P = "access_guard_v1";
    private static final String KEY_KIND = "kind";
    private static final String KEY_SALT = "salt";
    private static final String KEY_HASH = "hash";
    private static final String KEY_FAILS = "fails";
    private static final String KEY_UNTIL = "until";
    private static final int ITERATIONS = 175000;

    private static SharedPreferences pref(Context context) {
        return context.getSharedPreferences(P, Context.MODE_PRIVATE);
    }
    static boolean enabled(Context context) {
        SharedPreferences sp = pref(context);
        return sp.contains(KEY_KIND) && sp.contains(KEY_SALT) && sp.contains(KEY_HASH);
    }
    static String kind(Context context) {
        return pref(context).getString(KEY_KIND, PIN);
    }
    static void save(Context context, String kind, char[] value) throws Exception {
        if (!(PIN.equals(kind) || PATTERN.equals(kind)) || !valid(kind, value)) {
            Arrays.fill(value, '\0');
            throw new IllegalArgumentException("Invalid access credential");
        }
        byte[] salt = new byte[24];
        new SecureRandom().nextBytes(salt);
        byte[] digest = derive(value, salt);
        try {
            boolean done = pref(context).edit()
                .putString(KEY_KIND, kind)
                .putString(KEY_SALT, Base64.encodeToString(salt, Base64.NO_WRAP))
                .putString(KEY_HASH, Base64.encodeToString(digest, Base64.NO_WRAP))
                .putInt(KEY_FAILS, 0)
                .putLong(KEY_UNTIL, 0L)
                .commit();
            if (!done) throw new IllegalStateException("Storage failed");
        } finally {
            Arrays.fill(value, '\0');
            Arrays.fill(digest, (byte)0);
        }
    }
    static boolean valid(String kind, char[] value) {
        if (value == null) return false;
        if (PIN.equals(kind)) {
            if (value.length < 6 || value.length > 8) return false;
            for (char ch : value) if (ch < '0' || ch > '9') return false;
            return true;
        }
        if (PATTERN.equals(kind)) {
            if (value.length < 4 || value.length > 9) return false;
            boolean[] seen = new boolean[9];
            for (char ch : value) {
                int n = ch - '1';
                if (n < 0 || n >= 9 || seen[n]) return false;
                seen[n] = true;
            }
            return true;
        }
        return false;
    }
    private static byte[] derive(char[] pass, byte[] salt) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(pass, salt, ITERATIONS, 256);
        try { return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded(); }
        finally { spec.clearPassword(); }
    }
    static long remainingMillis(Context context) {
        return Math.max(0L, pref(context).getLong(KEY_UNTIL, 0L) - System.currentTimeMillis());
    }
    static boolean verify(Context context, char[] value) {
        try {
            if (remainingMillis(context) > 0 || !enabled(context)) return false;
            byte[] salt = Base64.decode(pref(context).getString(KEY_SALT, ""), Base64.NO_WRAP);
            byte[] hash = Base64.decode(pref(context).getString(KEY_HASH, ""), Base64.NO_WRAP);
            byte[] candidate = derive(value, salt);
            boolean ok = MessageDigest.isEqual(candidate, hash);
            Arrays.fill(candidate, (byte)0);
            if (ok) {
                pref(context).edit().putInt(KEY_FAILS, 0).putLong(KEY_UNTIL, 0).commit();
            } else {
                int failures = Math.min(30, pref(context).getInt(KEY_FAILS, 0) + 1);
                long cooldown = failures < 5 ? 0L :
                    failures < 10 ? 30_000L : failures < 15 ? 120_000L : 300_000L;
                pref(context).edit().putInt(KEY_FAILS, failures)
                    .putLong(KEY_UNTIL, cooldown == 0 ? 0L : System.currentTimeMillis() + cooldown).commit();
            }
            return ok;
        } catch (Exception error) { return false; }
        finally { if (value != null) Arrays.fill(value, '\0'); }
    }
    static void clear(Context context) {
        pref(context).edit().clear().commit();
    }
}