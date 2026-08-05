# Platform Architecture

```text
                    Seymour Platform
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   SPI Runtime       Service Registry   Nexus Command Center
        |                  |                  |
        +------------------+------------------+
                           |
      +--------------------+--------------------+
      |                    |                    |
      v                    v                    v
Blockchain Platform   Mining Platform      Pool Platform
```

## Lifecycle flow

```text
Discover -> Plan -> Provision -> Configure -> Verify -> Register -> Healthy
```

## Responsibility rule

SPI orchestrates lifecycle. Products own their domains. Nexus observes and operates through published contracts.
