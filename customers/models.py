from django.db import models

class Customer(models.Model):
    name = models.CharField("Nome", max_length=160)
    code = models.SlugField("Código", max_length=60, unique=True)
    active = models.BooleanField("Ativo", default=True)

    ksc_host = models.CharField("Servidor KSC", max_length=255)
    ksc_port = models.PositiveIntegerField("Porta OpenAPI", default=13299)
    timezone = models.CharField("Timezone", max_length=80, default="America/Sao_Paulo")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.name
