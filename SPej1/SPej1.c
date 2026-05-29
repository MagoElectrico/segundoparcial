#include <stdint.h>
#include <stdbool.h>
#include "inc/hw_ints.h"
#include "inc/hw_memmap.h"
#include "inc/hw_types.h"
#include "driverlib/sysctl.h"
#include "driverlib/gpio.h"
#include "driverlib/uart.h"
#include "driverlib/timer.h"
#include "driverlib/interrupt.h"
#include "driverlib/pin_map.h" 

// Variables Globales para Control de Estado
volatile char estado_actual = 'X';    // 'C' = Coca, 'S' = Salvietti, 'X' = Ninguno
volatile uint32_t periodo_actual = 3;  // Inicia en 3 segundos por defecto
uint32_t frecuencia_reloj;             // Guardará de forma segura los 120 MHz del sistema

// Prototipos de Funciones
void ConfigurarSistema(void);
void UART7_Handler(void);
void Timer0A_Handler(void);
void ActualizarPeriodoTimer(uint32_t segundos);

int main(void) {
    // Configurar Reloj, GPIO, UART7 y Timer0A
    ConfigurarSistema();

    while(1) {
        // El bucle principal queda libre. Toda la lógica corre en segundo plano
        // mediante interrupciones de hardware.
    }
}

// ==============================================================================
// CONFIGURACIÓN DE PERIFÉRICOS
// ==============================================================================
void ConfigurarSistema(void) {
    // 1. Configurar reloj del sistema a 120 MHz de forma correcta y almacenar el retorno
    frecuencia_reloj = SysCtlClockFreqSet((SYSCTL_XTAL_25MHZ | SYSCTL_OSC_MAIN | SYSCTL_USE_PLL | SYSCTL_CFG_VCO_480), 120000000);

    // 2. Habilitar periféricos (Puerto F para LEDs, Puerto C para UART7, UART7 y Timer0)
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOC);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_UART7);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_TIMER0);

    // Esperar un momento a que los periféricos estén listos y estables
    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOF) || 
          !SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOC) || 
          !SysCtlPeripheralReady(SYSCTL_PERIPH_UART7) || 
          !SysCtlPeripheralReady(SYSCTL_PERIPH_TIMER0)) {
        // Espera de seguridad obligatoria a 120MHz
    }

    // 3. Configurar LEDs del Puerto F (PF1 = Rojo, PF3 = Verde) como salidas
    GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3);
    GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3, 0x00); // Apagar ambos inicialmente

    // 4. Configurar Pines PC4 (Rx) y PC5 (Tx) para el UART7
    GPIOPinConfigure(GPIO_PC4_U7RX);
    GPIOPinConfigure(GPIO_PC5_U7TX);
    GPIOPinTypeUART(GPIO_PORTC_BASE, GPIO_PIN_4 | GPIO_PIN_5);

    // 5. Configurar UART7 a 9600 baudios usando la variable segura "frecuencia_reloj"
    UARTConfigSetExpClk(UART7_BASE, frecuencia_reloj, 9600,(UART_CONFIG_WLEN_8 | UART_CONFIG_STOP_ONE | UART_CONFIG_PAR_NONE));

    // 6. Habilitar Interrupciones de Recepción (Rx) en UART7
    IntEnable(INT_UART7);
    UARTIntEnable(UART7_BASE, UART_INT_RX | UART_INT_RT);

    // 7. Configurar Timer 0A como periódico de 32 bits completo
    TimerConfigure(TIMER0_BASE, TIMER_CFG_PERIODIC);
    
    // Cargar periodo inicial: 3 segundos por defecto (frecuencia_reloj * 3)
    TimerLoadSet(TIMER0_BASE, TIMER_A, (frecuencia_reloj * periodo_actual) - 1);

    // Habilitar Interrupción del Timer 0A
    IntEnable(INT_TIMER0A);
    TimerIntEnable(TIMER0_BASE, TIMER_TIMA_TIMEOUT);

    // 8. Habilitar interrupciones globales del procesador
    IntMasterEnable();

    // Arrancar el Timer
    TimerEnable(TIMER0_BASE, TIMER_A);
}

// ==============================================================================
// RUTINA DE INTERRUPCIÓN: UART7 (Recibe los datos de la Raspberry Pi)
// ==============================================================================
void UART7_Handler(void) {
    uint32_t ui32Status;
    char dato_recibido;

    // Obtener la causa de la interrupción y limpiarla
    ui32Status = UARTIntStatus(UART7_BASE, true);
    UARTIntClear(UART7_BASE, ui32Status);

    // Leer todos los caracteres disponibles en el búfer de entrada
    while(UARTCharsAvail(UART7_BASE)) {
        dato_recibido = (char)UARTCharGetNonBlocking(UART7_BASE);
        
        // Evitar procesar datos repetidos innecesariamente
        if (dato_recibido == estado_actual) {
            continue; 
        }

        estado_actual = dato_recibido;

        // Evaluar el comando recibido según las reglas del laboratorio
        if (estado_actual == 'C') {
            ActualizarPeriodoTimer(1); // Coca-Cola -> Parpadeo 1 segundo
        } 
        else if (estado_actual == 'S') {
            ActualizarPeriodoTimer(1); // Salvietti -> Parpadeo 1 segundo
        } 
        else {
            ActualizarPeriodoTimer(3); // 'X' u otro -> Parpadeo 3 segundos
        }
    }
}

// ==============================================================================
// RUTINA DE INTERRUPCIÓN: TIMER 0A (Maneja el parpadeo en el intervalo correcto)
// ==============================================================================
void Timer0A_Handler(void) {
    // Limpiar la interrupción por timeout del Timer
    TimerIntClear(TIMER0_BASE, TIMER_TIMA_TIMEOUT);

    // Leer el estado actual de los pines de salida de los LEDs
    uint32_t led_estado_actual = GPIOPinRead(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3);

    // Aplicar la lógica de encendido/conmutación basada en el objeto detectado
    if (estado_actual == 'C') {
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, 0x00); 
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1, led_estado_actual ^ GPIO_PIN_1);
    } 
    else if (estado_actual == 'S') {
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1, 0x00); 
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, led_estado_actual ^ GPIO_PIN_3);
    } 
    else {
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3, led_estado_actual ^ (GPIO_PIN_1 | GPIO_PIN_3));
    }
}

// ==============================================================================
// FUNCIÓN AUXILIAR: RECONFIGURACIÓN DINÁMICA DEL TEMPORIZADOR
// ==============================================================================
void ActualizarPeriodoTimer(uint32_t segundos) {
    periodo_actual = segundos;
    
    // Deshabilitar temporalmente el timer para cambiar el periodo de forma segura
    TimerDisable(TIMER0_BASE, TIMER_A);
    
    // Cargar el nuevo valor usando "frecuencia_reloj" en vez de SysCtlClockGet()
    TimerLoadSet(TIMER0_BASE, TIMER_A, (frecuencia_reloj * periodo_actual) - 1);
    
    // Apagar los LEDs inmediatamente al cambiar de botella para limpiar el estado visual
    GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3, 0x00);
    
    // Volver a encender el Timer con el nuevo intervalo establecido
    TimerEnable(TIMER0_BASE, TIMER_A);
}