# ADR-001: Arquitectura Local Filesystem-Based

## Estado
Aceptado

## Contexto
El Charter especifica explícitamente que el hosting/infraestructura en la nube está **Out-of-Scope** para DevHub v1.0. Esta restricción requiere definir una arquitectura que funcione completamente en entornos locales.

## Decisión
Implementar DevHub con arquitectura **filesystem-based local**:
- Persistencia mediante archivos YAML/Markdown locales
- No dependencias de bases de datos externas
- No requerimientos de conectividad a la nube
- Ejecución completa en máquina del desarrollador

## Rationale
1. **Alineación Charter**: Cumple restricción explícita "No hosting en nube"
2. **Simplicidad**: Reduce complejidad operacional y dependencias
3. **Portabilidad**: Funciona en cualquier entorno con Python + Git
4. **Control**: Usuario mantiene control total de sus datos
5. **Performance**: Acceso directo a filesystem es más rápido que red

## Consecuencias

### Positivas
- ✅ Zero setup infrastructure
- ✅ Funciona offline completamente
- ✅ Control total de datos por usuario
- ✅ Backup simple (Git + filesystem)
- ✅ No costos de hosting

### Negativas  
- ❌ No colaboración real-time entre máquinas
- ❌ Backup manual requerido
- ❌ Escalabilidad limitada por I/O local
- ❌ No centralización de métricas

### Mitigaciones
- Git para versionado y colaboración asíncrona
- Scripts de backup automático
- Optimización I/O con caching
- Export de métricas para agregación externa

## Fecha
2025-08-09

## Revisar
Cuando se considere DevHub v2.0 con capacidades cloud