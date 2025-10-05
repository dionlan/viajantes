import { Component, Input, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-date-picker',
    standalone: true,
    imports: [CommonModule, FormsModule],
    template: `
    <div class="relative">
      <div class="absolute left-4 top-1/2 transform -translate-y-1/2 text-blue-500">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <input
        type="date"
        [value]="value || ''"
        (input)="onDateChange($event)"
        [min]="minDate"
        [max]="maxDate"
        class="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-300 pl-12"
      />
      <button 
        *ngIf="value"
        (click)="clearDate()"
        class="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-red-500 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  `,
    styles: [`
    input[type="date"]::-webkit-calendar-picker-indicator {
      opacity: 0;
      position: absolute;
      width: 100%;
      height: 100%;
      left: 0;
      cursor: pointer;
    }
    input[type="date"]::-webkit-inner-spin-button,
    input[type="date"]::-webkit-clear-button {
      display: none;
    }
  `]
})
export class DatePickerComponent {
    @Input() value: string | null = null;
    @Input() minDate: string | null = null;
    @Input() maxDate: string | null = null;
    @Input() placeholder: string = 'Selecione uma data';
    @Output() valueChange = new EventEmitter<string | null>();

    onDateChange(event: Event) {
        const value = (event.target as HTMLInputElement).value;
        this.valueChange.emit(value || null);
    }

    clearDate() {
        this.valueChange.emit(null);
    }

    get displayValue(): string {
        return this.value ? new Date(this.value).toLocaleDateString() : this.placeholder;
    }
}