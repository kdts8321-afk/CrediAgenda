package mx.crediagenda.app;

import java.util.Arrays;
import java.util.List;

final class VerifyBalance29 {
    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        Models.Payment bbva = new Models.Payment(1, 1, 135099L, "2026-11-15", false, 101, 11);
        Models.Payment amex = new Models.Payment(2, 2, 90000L, "2026-11-26", true, 102, 11);
        List<Models.Payment> items = Arrays.asList(bbva, amex);

        check(PaymentRules.pendingCents(items) == 135099L, "Solo pendiente debe sumar saldo");
        check(PaymentRules.isPending(bbva), "El pago pendiente tiene saldo");
        check(!PaymentRules.isPending(amex), "El pago liquidado no tiene saldo");
        check(bbva.amountCents == 135099L && amex.amountCents == 90000L,
            "Los importes registrados nunca deben cambiar");

        bbva.paid = true;
        check(PaymentRules.pendingCents(items) == 0L, "Ya pagué debe quitar del pendiente");
        check(!PaymentRules.isPending(bbva), "El pago realizado no muestra saldo");
        check(bbva.amountCents == 135099L && bbva.eventId == 101,
            "Marcar pagado conserva importe e identificador del evento");

        bbva.paid = false;
        check(PaymentRules.pendingCents(items) == 135099L,
            "Volver a Pendiente debe restaurar saldo original");
        check(PaymentRules.isPending(bbva), "Volver a Pendiente muestra saldo");
        check(bbva.amountCents == 135099L, "El importe debe permanecer intacto");

        amex.paid = false;
        check(PaymentRules.pendingCents(items) == 225099L,
            "Suma múltiple de pagos pendientes");
        System.out.println("Personal 2.9: 10 verificaciones de saldos y preservación de importes OK");
    }
}
