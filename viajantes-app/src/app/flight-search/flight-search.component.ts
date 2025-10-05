// flight-search.component.ts
import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { FlightService } from '../service/flight.service';
import { DatePickerComponent } from '../components/date-picker.component';

@Component({
    selector: 'app-flight-search',
    standalone: true,
    imports: [CommonModule, FormsModule, DatePickerComponent],
    templateUrl: './flight-search.component.html',
    styleUrls: ['./flight-search.component.scss']
})
export class FlightSearchComponent {
    constructor(private flightService: FlightService) { }

    flightType = signal<'one-way' | 'round-trip'>('round-trip');
    cabinClass = signal<'economy' | 'business'>('economy');
    passengers = signal({
        adults: 1,
        children: 0,
        infants: 0
    });

    origin = signal('');
    destination = signal('');
    departureDate = signal<string | null>(null);
    returnDate = signal<string | null>(null);
    dateRange = signal<Date[] | null>(null);

    // Calcula datas mínimas/máximas
    today = new Date().toISOString().split('T')[0];
    maxDate = new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().split('T')[0];


    // Mock data for autocomplete
    airports = [
        { code: 'BSB', name: 'Brasília', city: 'Brasília' },
        { code: 'GRU', name: 'Guarulhos', city: 'São Paulo' },
        { code: 'GIG', name: 'Galeão', city: 'Rio de Janeiro' },
        { code: 'CGH', name: 'Congonhas', city: 'São Paulo' },
        { code: 'SSA', name: 'Deputado Luís Eduardo Magalhães', city: 'Salvador' },
        { code: 'REC', name: 'Guararapes', city: 'Recife' },
        { code: 'POA', name: 'Salgado Filho', city: 'Porto Alegre' },
        { code: 'CNF', name: 'Tancredo Neves', city: 'Belo Horizonte' }
    ];

    filteredOrigins = signal(this.airports);
    filteredDestinations = signal(this.airports);

    showPassengerPicker = signal(false);
    showDatePicker = signal(false);

    updateOrigin(event: Event) {
        const value = (event.target as HTMLInputElement).value;
        this.origin.set(value);
        this.filteredOrigins.set(
            this.airports.filter(airport =>
                `${airport.city} ${airport.name} ${airport.code}`
                    .toLowerCase()
                    .includes(value.toLowerCase())
            )
        );
    }

    updateDestination(event: Event) {
        const value = (event.target as HTMLInputElement).value;
        this.destination.set(value);
        this.filteredDestinations.set(
            this.airports.filter(airport =>
                `${airport.city} ${airport.name} ${airport.code}`
                    .toLowerCase()
                    .includes(value.toLowerCase())
            )
        );
    }

    selectAirport(type: 'origin' | 'destination', airport: any) {
        if (type === 'origin') {
            this.origin.set(`${airport.city}, ${airport.name} (${airport.code})`);
        } else {
            this.destination.set(`${airport.city}, ${airport.name} (${airport.code})`);
        }
    }

    togglePassengerPicker() {
        this.showPassengerPicker.update(prev => !prev);
    }

    adjustPassengers(type: 'adults' | 'children' | 'infants', delta: number) {
        const current = this.passengers();
        const newValue = Math.max(0, current[type] + delta);

        // Garante pelo menos 1 adulto
        if (type === 'adults' && newValue < 1) return;

        this.passengers.set({ ...current, [type]: newValue });
    }

    searchFlights() {
        // Validação dos dados
        if (!this.origin() || !this.destination() || !this.departureDate()) {
            console.error('Origem, destino e data de ida são obrigatórios');
            return;
        }

        // Extrai códigos dos aeroportos
        const originCode = this.extractAirportCode(this.origin());
        const destinationCode = this.extractAirportCode(this.destination());

        if (!originCode || !destinationCode) {
            console.error('Códigos de aeroporto inválidos');
            return;
        }

        // Prepara parâmetros
        const searchParams = {
            origin: originCode,
            destination: destinationCode,
            departureDate: this.departureDate(),
            returnDate: this.flightType() === 'round-trip' ? this.returnDate() : undefined,
            passengers: this.passengers().adults + this.passengers().children + this.passengers().infants,
            cabinClass: this.cabinClass()
        };

        // Chama o serviço
        this.flightService.searchFlights(searchParams).subscribe({
            next: (response) => {
                if (response.success) {
                    console.log('Voos encontrados:', response.data);
                    // Atualize sua interface com os resultados
                } else {
                    console.warn(response.message);
                }
            },
            error: (err) => {
                console.error('Erro na busca:', err);
                // Mostre uma mensagem de erro para o usuário
            }
        });
    }

    private extractAirportCode(fullText: string): string {
        // Extrai o código do aeroporto do texto completo (ex: "São Paulo, Guarulhos (GRU)" => "GRU")
        const match = fullText.match(/\(([A-Z]{3})\)/);
        return match ? match[1] : fullText;
    }

    get minReturnDate(): string | null {
        return this.departureDate() ? this.departureDate() : this.today;
    }
}