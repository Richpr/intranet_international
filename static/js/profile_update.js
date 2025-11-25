// static/js/profile_update.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation Flatpickr (Dates)
    if (typeof flatpickr === "function") {
        flatpickr(".datepicker", { dateFormat: "Y-m-d" });
    }

    const phoneInputField = document.querySelector("#id_phone_number");
    
    if (phoneInputField) {
        // Configuration intl-tel-input
        const phoneInput = window.intlTelInput(phoneInputField, {
            utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js",
            initialCountry: "auto",
            geoIpLookup: function(callback) {
                fetch("https://ipapi.co/json")
                    .then((res) => res.json())
                    .then((data) => callback(data.country_code))
                    .catch(() => callback("bj"));
            },
            preferredCountries: ["bj", "tg", "ci", "sn", "fr"],
            separateDialCode: true, // Affiche le +229 à gauche
        });

        // FONCTION CLÉ : Met à jour la valeur input avec le format international (+229...)
        function updatePhoneNumber() {
            if (phoneInput.isValidNumber()) {
                // getNumber() retourne le format E.164 (ex: +22990457845)
                const fullNumber = phoneInput.getNumber();
                
                // On ne modifie la valeur que si elle est différente pour éviter de gêner la saisie
                if (phoneInputField.value !== fullNumber) {
                    phoneInputField.value = fullNumber;
                    console.log("Numéro converti pour envoi : " + fullNumber);
                }
                phoneInputField.classList.remove("is-invalid");
                phoneInputField.classList.add("is-valid");
            }
        }

        // 1. Déclenche la mise à jour quand on quitte le champ (blur)
        // C'est plus sûr que de le faire au submit
        phoneInputField.addEventListener("blur", updatePhoneNumber);

        // 2. Déclenche aussi quand on survole le bouton d'envoi (sécurité supplémentaire)
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.addEventListener("mouseenter", updatePhoneNumber);
        }

        // Gestion du submit final pour nettoyer les erreurs
        const form = phoneInputField.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                // On essaie de récupérer le numéro au format international
                const fullNumber = phoneInput.getNumber();
                
                // Si la librairie a pu formater un numéro (même s'il n'est pas "valide"),
                // on met à jour le champ pour que le backend reçoive le format international.
                if (fullNumber) {
                    phoneInputField.value = fullNumber;
                }
                
                // On laisse le backend faire la validation finale.
                // Le javascript ne bloque plus la soumission.
            });
        }
    }
});