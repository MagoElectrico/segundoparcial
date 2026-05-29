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
#include "driverlib/pwm.h" 

volatile char estado_actual = 'X';    
volatile char ultima_soda = 'C';       
volatile uint32_t periodo_actual = 3;  
uint32_t frecuencia_reloj;             

void ConfigurarSistema(void);
void UART7_Handler(void);
void Timer0A_Handler(void);
void ActualizarPeriodoTimer(uint32_t segundos);

int main(void) {
    ConfigurarSistema();
    while(1) {
    }
}

void ConfigurarSistema(void) {
    frecuencia_reloj = SysCtlClockFreqSet((SYSCTL_XTAL_25MHZ | SYSCTL_OSC_MAIN | SYSCTL_USE_PLL | SYSCTL_CFG_VCO_480), 120000000);
    
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOC);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_UART7);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_TIMER0);
    SysCtlPeripheralEnable(SYSCTL_PERIPH_PWM0); 

    while(!SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOF) || 
          !SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOC) || 
          !SysCtlPeripheralReady(SYSCTL_PERIPH_UART7) || 
          !SysCtlPeripheralReady(SYSCTL_PERIPH_TIMER0) ||
          !SysCtlPeripheralReady(SYSCTL_PERIPH_PWM0)) {
    }

    GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3);
    GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3, 0x00);

    GPIOPinConfigure(GPIO_PC4_U7RX);
    GPIOPinConfigure(GPIO_PC5_U7TX);
    GPIOPinTypeUART(GPIO_PORTC_BASE, GPIO_PIN_4 | GPIO_PIN_5);
    UARTConfigSetExpClk(UART7_BASE, frecuencia_reloj, 9600,(UART_CONFIG_WLEN_8 | UART_CONFIG_STOP_ONE | UART_CONFIG_PAR_NONE));
    IntEnable(INT_UART7);
    UARTIntEnable(UART7_BASE, UART_INT_RX | UART_INT_RT);

    GPIOPinConfigure(GPIO_PF2_M0PWM2);
    GPIOPinTypePWM(GPIO_PORTF_BASE, GPIO_PIN_2);
    PWMGenConfigure(PWM0_BASE, PWM_GEN_1, PWM_GEN_MODE_DOWN | PWM_GEN_MODE_NO_SYNC);
    PWMGenPeriodSet(PWM0_BASE, PWM_GEN_1, 120000); 
    
    PWMPulseWidthSet(PWM0_BASE, PWM_OUT_2, 1); 
    PWMOutputState(PWM0_BASE, PWM_OUT_2_BIT, true);
    PWMGenEnable(PWM0_BASE, PWM_GEN_1);

    TimerConfigure(TIMER0_BASE, TIMER_CFG_PERIODIC);
    TimerLoadSet(TIMER0_BASE, TIMER_A, (frecuencia_reloj * periodo_actual) - 1);
    IntEnable(INT_TIMER0A);
    TimerIntEnable(TIMER0_BASE, TIMER_TIMA_TIMEOUT);

    IntMasterEnable();
    TimerEnable(TIMER0_BASE, TIMER_A);
}

void UART7_Handler(void) {
    uint32_t ui32Status;
    char dato_recibido;

    ui32Status = UARTIntStatus(UART7_BASE, true);
    UARTIntClear(UART7_BASE, ui32Status);

    while(UARTCharsAvail(UART7_BASE)) {
        dato_recibido = (char)UARTCharGetNonBlocking(UART7_BASE);
        
        if (dato_recibido != 'C' && dato_recibido != 'S' && dato_recibido != 'X' && dato_recibido != 'M') {
            continue; 
        }

        if (dato_recibido == estado_actual) {
            continue; 
        }
        
        estado_actual = dato_recibido;

        if (estado_actual == 'C') {
            ultima_soda = 'C';      
            PWMPulseWidthSet(PWM0_BASE, PWM_OUT_2, 1); // 1 = Apagado total
            ActualizarPeriodoTimer(1);                 
        } 
        else if (estado_actual == 'S') {
            ultima_soda = 'S';      
            PWMPulseWidthSet(PWM0_BASE, PWM_OUT_2, 1); // 1 = Apagado total
            ActualizarPeriodoTimer(1);                 
        } 
        else if (estado_actual == 'X') {
            PWMPulseWidthSet(PWM0_BASE, PWM_OUT_2, 1); // 1 = Apagado total
            ActualizarPeriodoTimer(3);                 
        }
        else if (estado_actual == 'M') {
            PWMPulseWidthSet(PWM0_BASE, PWM_OUT_2, 60000); // 60000 = 50% Encendido
            ActualizarPeriodoTimer(3);                     
        }
    }
}

void Timer0A_Handler(void) {
    TimerIntClear(TIMER0_BASE, TIMER_TIMA_TIMEOUT);

    uint32_t led_estado_actual = GPIOPinRead(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3);

    if (ultima_soda == 'C') {
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, 0x00); 
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1, led_estado_actual ^ GPIO_PIN_1);
    } 
    else if (ultima_soda == 'S') {
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1, 0x00); 
        GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, led_estado_actual ^ GPIO_PIN_3);
    } 
}

void ActualizarPeriodoTimer(uint32_t segundos) {
    periodo_actual = segundos;
    TimerDisable(TIMER0_BASE, TIMER_A);
    TimerLoadSet(TIMER0_BASE, TIMER_A, (frecuencia_reloj * periodo_actual) - 1);
    GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_1 | GPIO_PIN_3, 0x00);
    TimerEnable(TIMER0_BASE, TIMER_A);
}
