import express from 'express'; // funciona agora com esModuleInterop
import { Request, Response, NextFunction } from 'express';

const app = express();

app.use('/**', (req: Request, res: Response, next: NextFunction) => {
  res.send('Servidor Express respondendo!');
});

app.listen(3000, () => {
  console.log('Servidor rodando na porta 3000');
});
