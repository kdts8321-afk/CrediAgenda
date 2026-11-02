package mx.crediagenda.app;

import android.app.Activity;
import android.content.Context;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.CancellationSignal;
import java.util.concurrent.atomic.AtomicBoolean;

/** Autenticación local con la ventana segura proporcionada por Android. No almacena biometría. */
final class BiometricAccess {
    private static final String PREFS = "personal_biometric_access_26";
    private static final String ENABLED = "enabled";

    static boolean enabled(Context c) {
        return AccessGuard.enabled(c) && c.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getBoolean(ENABLED, false);
    }

    static void setEnabled(Context c, boolean value) {
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(ENABLED, value).commit();
    }

    static void clear(Context c) {
        c.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().commit();
    }

    static boolean available(Context c) {
        if (Build.VERSION.SDK_INT < 28) return false;
        try {
            if (Build.VERSION.SDK_INT >= 30) {
                android.hardware.biometrics.BiometricManager manager =
                    c.getSystemService(android.hardware.biometrics.BiometricManager.class);
                return manager != null && manager.canAuthenticate(
                    android.hardware.biometrics.BiometricManager.Authenticators.BIOMETRIC_WEAK |
                    android.hardware.biometrics.BiometricManager.Authenticators.BIOMETRIC_STRONG)
                    == android.hardware.biometrics.BiometricManager.BIOMETRIC_SUCCESS;
            }
            if (Build.VERSION.SDK_INT >= 29) {
                android.hardware.biometrics.BiometricManager manager =
                    c.getSystemService(android.hardware.biometrics.BiometricManager.class);
                return manager != null && manager.canAuthenticate()
                    == android.hardware.biometrics.BiometricManager.BIOMETRIC_SUCCESS;
            }
            // Android 9: huella inscrita en el sistema (el soporte facial depende del fabricante).
            android.hardware.fingerprint.FingerprintManager fm =
                (android.hardware.fingerprint.FingerprintManager)
                    c.getSystemService(Context.FINGERPRINT_SERVICE);
            return fm != null && fm.isHardwareDetected() && fm.hasEnrolledFingerprints();
        } catch (Exception ignored) {
            return false;
        }
    }

    static CancellationSignal prompt(Activity a, Runnable success, Runnable failure) {
        if (!available(a) || Build.VERSION.SDK_INT < 28) {
            failure.run();
            return null;
        }
        final AtomicBoolean finished = new AtomicBoolean(false);
        Runnable onFailure = () -> {
            if (finished.compareAndSet(false, true)) failure.run();
        };
        Runnable onSuccess = () -> {
            if (finished.compareAndSet(false, true)) success.run();
        };
        try {
            android.hardware.biometrics.BiometricPrompt.Builder builder =
                new android.hardware.biometrics.BiometricPrompt.Builder(a)
                    .setTitle("Desbloquear Personal")
                    .setSubtitle("Utiliza la huella o rostro registrados en tu teléfono")
                    .setNegativeButton("Usar PIN o patrón", a.getMainExecutor(),
                        (dialog, which) -> onFailure.run());
            if (Build.VERSION.SDK_INT >= 30) {
                builder.setAllowedAuthenticators(
                    android.hardware.biometrics.BiometricManager.Authenticators.BIOMETRIC_WEAK |
                    android.hardware.biometrics.BiometricManager.Authenticators.BIOMETRIC_STRONG);
            }
            android.hardware.biometrics.BiometricPrompt prompt = builder.build();
            CancellationSignal signal = new CancellationSignal();
            prompt.authenticate(signal, a.getMainExecutor(),
                new android.hardware.biometrics.BiometricPrompt.AuthenticationCallback() {
                    @Override
                    public void onAuthenticationSucceeded(
                            android.hardware.biometrics.BiometricPrompt.AuthenticationResult result) {
                        onSuccess.run();
                    }

                    @Override
                    public void onAuthenticationError(int errorCode, CharSequence errString) {
                        onFailure.run();
                    }
                    // Los intentos fallidos no desbloquean; Android permite nuevos intentos
                    // y gestiona los bloqueos biométricos del sistema.
                });
            return signal;
        } catch (Exception ex) {
            onFailure.run();
            return null;
        }
    }
}
