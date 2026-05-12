"""
Módulo SIEM — Correlación basada en reglas multicriterio.

Recibe:
    - Las predicciones generadas por ids.py
    - El DataFrame limpio con las características originales

Devuelve:
    - Un DataFrame enriquecido con:
        severidad
        recomendacion
"""

import pandas as pd


PESOS_ATAQUE = {
    "BENIGN": 0,

    "Reconnaissance": 1,
    "Analysis": 1,
    "Generic": 1,

    "PortScan": 2,
    "Fuzzers": 2,
    "FTP-Patator": 2,
    "Web Attack Brute Force": 2,

    "SSH-Patator": 3,
    "DoS slowloris": 3,
    "DoS Slowhttptest": 3,
    "DoS GoldenEye": 3,
    "DoS": 3,
    "Web Attack XSS": 3,

    "Web Attack Sql Injection": 4,
    "DoS Hulk": 4,
    "DDoS": 4,
    "Exploits": 4,
    "Bot": 4,

    "Heartbleed": 5,
    "Shellcode": 5,
    "Backdoor": 5,
    "Infiltration": 5,
    "Worms": 5,
}


RECOMENDACIONES_ATAQUE = {
 
    "Reconnaissance": (
        "Registrar IP origen y correlacionar con eventos anteriores. Considerar bloqueo preventivo si el comportamiento persiste. "
        "Aumentar nivel de vigilancia ante futuros eventos de la misma fuente."
    ),
 
    "Analysis": (
        "Revisar logs de la IP origen. Correlacionar con otros eventos del mismo lote o sesión."
    ),
 
    "Generic": (
        "Revisar tráfico asociado. Aplicar reglas de firewall sobre IP origen si el comportamiento es recurrente."
    ),
 
    "PortScan": (
        "Registrar IP origen y puertos escaneados. Cerrar puertos innecesarios expuestos al exterior. "
        "Considerar bloqueo temporal de la IP si el escaneo es agresivo o repetido."
    ),
 
    "Fuzzers": (
        "Revisar logs de aplicación en busca de errores inusuales o crashes. Comprobar si algún endpoint ha respondido de forma anómala. "
        "El fuzzing activo puede revelar vulnerabilidades explotables posteriormente."
    ),
 
    "FTP-Patator": (
        "Bloquear IP origen. Revisar intentos de autenticación fallidos en el servidor FTP. "
        "Forzar cambio de credenciales de todas las cuentas FTP activas. "
        "Considerar deshabilitar FTP y migrar a SFTP o FTPS si no se requiere acceso anónimo."
    ),
 
    "Web Attack Brute Force": (
        "Bloquear IP origen. Activar CAPTCHA y política de bloqueo de cuentas tras N intentos. "
        "Revisar cuentas con acceso reciente y forzar cambio de contraseña. Considerar autenticación multifactor (MFA) en los accesos críticos."
    ),
 
    "SSH-Patator": (
        "Bloquear IP origen. Revisar intentos de autenticación SSH. "
        "Deshabilitar autenticación por contraseña y usar exclusivamente clave pública. "
        "Considerar cambiar el puerto SSH por defecto y aplicar fail2ban."
    ),
 
    "DoS slowloris": (
        "Bloquear IP origen. Reducir el timeout de conexiones HTTP inactivas en el servidor. "
        "Limitar el número máximo de conexiones simultáneas por IP."
    ),
 
    "DoS Slowhttptest": (
        "Bloquear IP origen. Reducir timeout de body HTTP en el servidor. Aplicar rate limiting por IP a nivel de servidor web o WAF."
    ),
 
    "DoS GoldenEye": (
        "Bloquear IP origen. Aplicar reglas WAF para limitar peticiones HTTP Keep-Alive anómalas. "
        "Revisar disponibilidad del servidor HTTP afectado."
    ),
 
    "DoS": (
        "Bloquear IP origen. Aplicar rate limiting en el perímetro. "
        "Revisar disponibilidad de los servicios afectados y activar alertas de disponibilidad si no están configuradas."
    ),

    "Web Attack XSS": (
        "Bloquear IP origen. Revisar y sanear todas las entradas de usuario en la aplicación web afectada. "
        "Implementar Content Security Policy (CSP) para limitar la ejecución de scripts no autorizados. "
        "Revisar sesiones activas por posible robo de cookies."
    ),
 
    "Web Attack Sql Injection": (
        "Bloquear IP origen inmediatamente. Revisar y sanear todas las consultas SQL "
        "de la aplicación usando consultas parametrizadas o prepared statements. "
        "Auditar la base de datos en busca de accesos o modificaciones no autorizadas. Activar WAF con reglas de protección SQLi."
    ),

    "DoS Hulk": (
        "Bloquear IP origen inmediatamente. Activar reglas de rate limiting agresivas en el WAF o firewall perimetral. "
        "Revisar logs Apache/Nginx en busca de patrones de URL repetitivos."
    ),
 
    "DDoS": (
        "Activar protocolo de mitigación DDoS. "
        "Contactar con el ISP para filtrado upstream si el volumen supera la capacidad de mitigación local. "
        "Aplicar BGP blackholing o anycast si está disponible. Revisar si el tráfico proviene de múltiples subredes coordinadas."
    ),
 
    "Exploits": (
        "Aislar el sistema afectado de la red. Intentar identificar el CVE explotado mediante análisis de los payloads capturados. "
        "Aplicar el parche de seguridad correspondiente o aplicar mitigaciones temporales si el parche no está disponible."
    ),
 
    "Bot": (
        "Aislar el host afectado de la red inmediatamente. Analizar procesos activos, conexiones de red y tareas programadas "
        "en busca de persistencia. Identificar el servidor C2 y bloquearlo a nivel de firewall y DNS. "
        "Realizar análisis forense completo antes de restaurar el sistema."
    ),
 
    "Heartbleed": (
        "Parchear OpenSSL a una versión no vulnerable de forma inmediata. Revocar y renovar todos los certificados SSL/TLS del servidor "
        "afectado. Invalidar todas las sesiones activas y forzar re-autenticación de usuarios. "
        "Considerar que claves privadas, contraseñas y tokens pueden haber sido expuestos. Rotar claves privadas comprometidas."
    ),
 
    "Shellcode": (
        "Aislar el sistema afectado inmediatamente. Realizar análisis forense completo: revisar procesos activos, módulos del kernel, "
        "conexiones de red y ficheros creados recientemente. Comprobar integridad de binarios del sistema con herramientas "
        "como Tripwire o AIDE. No restaurar el sistema sin confirmar el vector de entrada."
    ),
 
    "Backdoor": (
        "Aislar el sistema afectado inmediatamente. Identificar y eliminar el mecanismo "
        "de acceso persistente: revisar cuentas de usuario, claves SSH autorizadas, tareas programadas y servicios inusuales. "
        "Auditar todos los accesos recientes. Considerar reinstalación completa del sistema si no se puede garantizar su integridad. "
        "Revisar mecanismos de persistencia en registro, servicios y tareas programadas."
    ),
 
    "Infiltration": (
        "Activar protocolo de respuesta a incidentes de nivel crítico. Aislar el segmento de red afectado. "
        "Realizar análisis forense de todos los sistemas del segmento. "
        "Identificar el vector de entrada inicial y el alcance del movimiento lateral. "
        "Notificar al responsable de seguridad y, si procede, a las autoridades competentes."
    ),
 
    "Worms": (
        "Aislar inmediatamente el segmento de red afectado para contener la propagación. "
        "Escanear todos los hosts del segmento en busca de infección. Identificar el vector "
        "de propagación (vulnerabilidad explotada o credenciales comprometidas) y aplicar "
        "el parche correspondiente antes de reconectar los sistemas. "
        "Realizar análisis forense completo en los sistemas afectados. Desconectar temporalmente recursos compartidos si es necesario."
    ),
}


RECOMENDACIONES_SEVERIDAD = {
    "BAJA": (
        "No es un evento prioritario, aunque se recomienda mantener monitorización básica."
    ),

    "MEDIA": (
        "Requiere revisión por parte del analista para descartar compromiso real."
    ),

    "ALTA": (
        "Se recomienda actuación inmediata para evitar impacto sobre otros sistemas."
    ),

    "CRITICA": (
        "Incidente crítico. Activar protocolo de respuesta a incidentes de forma inmediata."
    ),
}


def generar_recomendacion(fila, severidad):
    """
    Se genera la recomendación de cada flujo tanto para los 5 casos especiales posibles como para los casos base.
    """
    ataque = fila["prediccion"]
    baja = fila["baja_confianza"]

    if severidad == "INFO" and ataque == "BENIGN":
        return "Tráfico legítimo. Es un verdadero negativo. Se puede ignorar."

    if severidad != "INFO" and ataque == "BENIGN":
        return "Predicción de tráfico legítimo dudosa. Puede ser un falso negativo. Revisar manualmente."
        
    if severidad == "INFO" and ataque != "BENIGN":
        return "Flujo clasificado como ataque erróneamente. Es un falso positivo. Se puede ignorar."
    
    recomendacion_base = RECOMENDACIONES_ATAQUE[ataque]

    texto_severidad = RECOMENDACIONES_SEVERIDAD.get(severidad, "")

    return recomendacion_base + " - " + texto_severidad


def calcular_severidad(puntuacion):
    """
    Convierte la puntuación multicriterio en severidad textual.
    """

    if puntuacion == 0:
        return "INFO"

    if 1 <= puntuacion <= 2:
        return "BAJA"

    if 3 <= puntuacion <= 4:
        return "MEDIA"

    if 5 <= puntuacion <= 7:
        return "ALTA"

    return "CRITICA"


def correlacionar_alertas(df_predicciones, df_limpio):
    """
    Enriquece las predicciones IDS con severidad y recomendaciones.

    Parámetros:
        df_predicciones → salida generada por ids.py
        df_limpio       → DataFrame original de características

    Devuelve:
        DataFrame enriquecido con:
            severidad
            recomendacion
    """

    if len(df_predicciones) != len(df_limpio):
        raise ValueError(
            "df_predicciones y df_limpio deben tener el mismo número de filas"
        )

    df = pd.concat(
        [
            df_predicciones.reset_index(drop=True),
            df_limpio.reset_index(drop=True),
        ],
        axis=1
    )

    puntuaciones = []
    

    ataques = df[df["prediccion"] != "BENIGN"].copy()

    conteo_ataques = ataques["prediccion"].value_counts()


    for _, fila in df.iterrows():

        puntuacion = 0

        ataque = fila["prediccion"]

        puntuacion += PESOS_ATAQUE.get(ataque, 1)

        if ataque != "BENIGN":

            if (
                fila["Flow Bytes/s"] > 1_000_000
                or (
                    fila["Total Fwd Packet"]
                    + fila["Total Bwd packets"]
                ) > 10_000
            ):
                puntuacion += 1

            if (
                fila["Flow Duration"] < 1000
                or fila["Bwd IAT Std"] < 0.01
            ):
                puntuacion += 1

            if (
                fila["Packet Length Max"] > 1400
                and fila["Fwd Packet Length Std"] > 200
            ):
                puntuacion += 1

            if (
                fila["PSH Flag Count"] > 10
                or fila["Down/Up Ratio"] > 10
                or fila["FWD Init Win Bytes"] <= 0
            ):
                puntuacion += 1

        if fila["baja_confianza"] == 1:

            if ataque == "BENIGN":
                puntuacion += 2

            else:
                puntuacion -= 1

        if ataque != "BENIGN":

            cantidad = conteo_ataques.get(ataque, 0)

            total_ataques = len(ataques)

            if total_ataques > 0:

                porcentaje = cantidad / total_ataques

                peso = PESOS_ATAQUE.get(ataque, 1)

                if (
                    porcentaje >= 0.40
                    and cantidad >= 5
                    and peso >= 2
                ):
                    puntuacion += 1

        puntuaciones.append(max(0, puntuacion))

    df["severidad"] = [calcular_severidad(p) for p in puntuaciones]

    df["recomendacion"] = [
        generar_recomendacion(fila, sev)
        for (_, fila), sev in zip(df.iterrows(), df["severidad"])
    ]

    columnas_finales = [
        "id_flujo",
        "id_lote",
        "prediccion",
        "confianza",
        "baja_confianza",
        "severidad",
        "recomendacion",
    ]

    return df[columnas_finales]

