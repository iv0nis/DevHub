'use client';

import { useParams, useRouter } from 'next/navigation';

export default function StepPage() {
  const { step } = useParams();
  const router = useRouter();
  const currentStep = parseInt(step as string);

  const handlePrevious = () => {
    if (currentStep > 1) {
      router.push(`/step/${currentStep - 1}`);
    }
  };

  const handleNext = () => {
    if (currentStep < 6) {
      router.push(`/step/${currentStep + 1}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header con progreso */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              MVP Wizard
            </h1>
            <div className="text-sm text-gray-600">
              Paso {currentStep} de 6
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex items-center">
              {[1, 2, 3, 4, 5, 6].map((num) => (
                <div key={num} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      num === currentStep
                        ? 'bg-blue-600 text-white'
                        : num < currentStep
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {num}
                  </div>
                  {num < 6 && (
                    <div
                      className={`w-12 h-1 mx-2 ${
                        num < currentStep ? 'bg-green-500' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Contenido principal */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-8">
        <StepContent step={currentStep} />
      </main>

      {/* Footer con navegación */}
      <footer className="bg-white border-t">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className={`px-6 py-2 rounded-lg font-medium ${
                currentStep === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Anterior
            </button>
            <button
              onClick={handleNext}
              disabled={currentStep === 6}
              className={`px-6 py-2 rounded-lg font-medium ${
                currentStep === 6
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {currentStep === 6 ? 'Finalizar' : 'Siguiente'}
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Componente para el contenido específico de cada paso
function StepContent({ step }: { step: number }) {
  switch (step) {
    case 1:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Nombre del Proyecto</h2>
          <p className="text-gray-600 mb-6">
            Comencemos creando tu proyecto. Ingresa un nombre descriptivo.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre del proyecto
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Mi Proyecto Increíble"
              />
            </div>
          </div>
        </div>
      );

    case 2:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Briefing del Proyecto</h2>
          <p className="text-gray-600 mb-6">
            Describe tu proyecto, objetivos y contexto.
          </p>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción del proyecto
              </label>
              <textarea
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe qué quieres construir..."
              />
            </div>
          </div>
        </div>
      );

    case 3:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Vista Previa - Charter</h2>
          <p className="text-gray-600 mb-6">
            Basado en tu briefing, aquí tienes el charter del proyecto.
          </p>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">Charter generado automáticamente</h3>
            <p className="text-sm text-gray-600">
              El contenido del charter aparecerá aquí basado en la información del paso anterior.
            </p>
          </div>
        </div>
      );

    case 4:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Vista Previa - Roadmap</h2>
          <p className="text-gray-600 mb-6">
            Roadmap del proyecto basado en el charter.
          </p>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">Roadmap generado automáticamente</h3>
            <p className="text-sm text-gray-600">
              El roadmap aparecerá aquí con las fases y milestones del proyecto.
            </p>
          </div>
        </div>
      );

    case 5:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Vista Previa - Blueprint</h2>
          <p className="text-gray-600 mb-6">
            Blueprint técnico del proyecto.
          </p>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium mb-2">Blueprint generado automáticamente</h3>
            <p className="text-sm text-gray-600">
              La arquitectura técnica y estructura del proyecto aparecerá aquí.
            </p>
          </div>
        </div>
      );

    case 6:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Finalización</h2>
          <p className="text-gray-600 mb-6">
            ¡Perfecto! Tu proyecto está listo. Aquí tienes un resumen final.
          </p>
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-medium text-green-800 mb-2">Proyecto Creado Exitosamente</h3>
              <p className="text-sm text-green-700">
                Tu proyecto ha sido configurado con todos los documentos necesarios.
              </p>
            </div>
          </div>
        </div>
      );

    default:
      return (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Paso no encontrado</h2>
          <p className="text-gray-600">
            Este paso del wizard no existe. Por favor, navega a un paso válido (1-6).
          </p>
        </div>
      );
  }
}