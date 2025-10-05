// src/app/services/flight-data.ts
export interface Flight {
    id: string;
    airline: string;
    flightNumber: string;
    origin: {
        code: string;
        city: string;
        name: string;
    };
    destination: {
        code: string;
        city: string;
        name: string;
    };
    departure: string;
    arrival: string;
    duration: string;
    price: number;
    seatsAvailable: number;
    cabinClass: 'economy' | 'business';
    stops: number;
    amenities: string[];
}

export interface FlightSearchParams {
    origin: string;
    destination: string;
    departureDate: Date | string | null;
    returnDate?: Date | string | null;
    passengers: number;
    cabinClass: 'economy' | 'business';
}

export interface FlightSearchResponse {
    success: boolean;
    data: Flight[];
    message: string;
}

export const MOCK_FLIGHTS: Flight[] = [
    {
        id: 'FL001',
        airline: 'LATAM',
        flightNumber: 'LA 1234',
        origin: {
            code: 'GRU',
            city: 'São Paulo',
            name: 'Guarulhos'
        },
        destination: {
            code: 'GIG',
            city: 'Rio de Janeiro',
            name: 'Galeão'
        },
        departure: '2025-08-15T08:00:00',
        arrival: '2025-08-15T09:15:00',
        duration: '1h15m',
        price: 450,
        seatsAvailable: 24,
        cabinClass: 'economy',
        stops: 0,
        amenities: ['bagagem de mão', 'serviço de bordo']
    },
    {
        id: 'FL002',
        airline: 'GOL',
        flightNumber: 'G3 5678',
        origin: {
            code: 'GRU',
            city: 'São Paulo',
            name: 'Guarulhos'
        },
        destination: {
            code: 'GIG',
            city: 'Rio de Janeiro',
            name: 'Galeão'
        },
        departure: '2025-08-15T10:30:00',
        arrival: '2025-08-15T11:45:00',
        duration: '1h15m',
        price: 520,
        seatsAvailable: 12,
        cabinClass: 'economy',
        stops: 0,
        amenities: ['bagagem de mão', 'bagagem despachada']
    },
    {
        id: 'FL003',
        airline: 'AZUL',
        flightNumber: 'AD 9012',
        origin: {
            code: 'GRU',
            city: 'São Paulo',
            name: 'Guarulhos'
        },
        destination: {
            code: 'GIG',
            city: 'Rio de Janeiro',
            name: 'Galeão'
        },
        departure: '2025-08-15T14:00:00',
        arrival: '2025-08-15T15:30:00',
        duration: '1h30m',
        price: 380,
        seatsAvailable: 8,
        cabinClass: 'economy',
        stops: 1,
        amenities: ['bagagem de mão']
    },
    {
        id: 'FL004',
        airline: 'LATAM',
        flightNumber: 'LA 3456',
        origin: {
            code: 'GRU',
            city: 'São Paulo',
            name: 'Guarulhos'
        },
        destination: {
            code: 'BSB',
            city: 'Brasília',
            name: 'Presidente Juscelino Kubitschek'
        },
        departure: '2025-08-15T07:30:00',
        arrival: '2025-08-15T09:00:00',
        duration: '1h30m',
        price: 680,
        seatsAvailable: 16,
        cabinClass: 'business',
        stops: 0,
        amenities: ['bagagem de mão', 'bagagem despachada', 'refeição', 'prioridade no embarque']
    },
    {
        id: 'FL005',
        airline: 'GOL',
        flightNumber: 'G3 7890',
        origin: {
            code: 'GRU',
            city: 'São Paulo',
            name: 'Guarulhos'
        },
        destination: {
            code: 'BSB',
            city: 'Brasília',
            name: 'Presidente Juscelino Kubitschek'
        },
        departure: '2025-08-15T12:15:00',
        arrival: '2025-08-15T13:45:00',
        duration: '1h30m',
        price: 720,
        seatsAvailable: 4,
        cabinClass: 'business',
        stops: 0,
        amenities: ['bagagem de mão', 'bagagem despachada', 'refeição']
    },
    {
        id: 'FL006',
        airline: 'AZUL',
        flightNumber: 'AD 3456',
        origin: {
            code: 'GIG',
            city: 'Rio de Janeiro',
            name: 'Galeão'
        },
        destination: {
            code: 'BSB',
            city: 'Brasília',
            name: 'Presidente Juscelino Kubitschek'
        },
        departure: '2025-08-16T09:00:00',
        arrival: '2025-08-16T10:45:00',
        duration: '1h45m',
        price: 590,
        seatsAvailable: 18,
        cabinClass: 'economy',
        stops: 0,
        amenities: ['bagagem de mão', 'serviço de bordo']
    },
    {
        id: 'FL007',
        airline: 'LATAM',
        flightNumber: 'LA 4567',
        origin: {
            code: 'GIG',
            city: 'Rio de Janeiro',
            name: 'Galeão'
        },
        destination: {
            code: 'GRU',
            city: 'São Paulo',
            name: 'Guarulhos'
        },
        departure: '2025-08-16T16:30:00',
        arrival: '2025-08-16T17:45:00',
        duration: '1h15m',
        price: 430,
        seatsAvailable: 22,
        cabinClass: 'economy',
        stops: 0,
        amenities: ['bagagem de mão', 'serviço de bordo']
    }
];