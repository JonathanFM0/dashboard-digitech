"""
Script de Migração de Dados Históricos
Lê arquivos Excel da pasta historico_dados/ e popula o Supabase

EXECUÇÃO:
    python migrate.py

PRÉ-REQUISITOS:
    1. Ter executado o script SQL no Supabase
    2. Ter arquivo .env com credenciais ou st.secrets configurado
    3. Ter arquivos .xlsx na pasta historico_dados/
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar caminho
BASE_DIR = Path(__file__).parent
HISTORICO_DIR = BASE_DIR / 'historico_dados'

def conectar_supabase():
    """Conecta ao Supabase usando variáveis de ambiente"""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL') or os.getenv('SUPABASE_PROJECT_URL')
        supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ ERRO: Credenciais do Supabase não encontradas.")
            print("Configure no arquivo .env ou em .streamlit/secrets.toml")
            return None
        
        client = create_client(supabase_url, supabase_key)
        print("✅ Conectado ao Supabase com sucesso!")
        return client
    
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None


def extrair_mes_ano(df_ocupacao: pd.DataFrame) -> str:
    """Extrai mês/ano dos dados de ocupação"""
    if df_ocupacao.empty or 'DATA' not in df_ocupacao.columns:
        return None
    
    df_ocupacao['DATA'] = pd.to_datetime(df_ocupacao['DATA'], errors='coerce')
    datas_validas = df_ocupacao['DATA'].dropna()
    
    if datas_validas.empty:
        return None
    
    # Pega o mês mais frequente (caso haja dados misturados)
    mes_ano = datas_validas.dt.strftime('%Y-%m').mode()[0]
    return mes_ano


def migrar_arquivo(client, arquivo_path: Path) -> dict:
    """Migra um único arquivo Excel para o Supabase"""
    resultado = {
        'arquivo': arquivo_path.name,
        'sucesso': False,
        'registros': 0,
        'erros': []
    }
    
    try:
        print(f"\n📄 Processando: {arquivo_path.name}")
        
        # Ler todas as abas
        xl = pd.ExcelFile(arquivo_path)
        abas_disponiveis = xl.sheet_names
        
        # Validar abas essenciais
        abas_esperadas = ['TURMAS', 'OCUPAÇÃO', 'DISCIPLINAS']
        abas_faltantes = [aba for aba in abas_esperadas if aba not in abas_disponiveis]
        
        if abas_faltantes:
            erro = f"Ausência das abas: {', '.join(abas_faltantes)}"
            print(f"   ⚠️ {erro}")
            resultado['erros'].append(erro)
            xl.close()
            return resultado
        
        # Extrair mês/ano da aba OCUPAÇÃO
        df_ocupacao_raw = pd.read_excel(xl, sheet_name='OCUPAÇÃO')
        mes_ano = extrair_mes_ano(df_ocupacao_raw)
        
        if not mes_ano:
            erro = "Não foi possível extrair mês/ano dos dados"
            print(f"   ⚠️ {erro}")
            resultado['erros'].append(erro)
            xl.close()
            return resultado
        
        print(f"   📅 Mês/Ano detectado: {mes_ano}")
        
        total_registros = 0
        
        # ==================== MIGRAR TURMAS ====================
        if 'TURMAS' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='TURMAS')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    client.table('turmas').upsert({
                        'id_turma': str(row.get('ID_TURMA', '')),
                        'nome_turma': str(row.get('NOME_TURMA', '')),
                        'turno': str(row.get('TURNO', '')),
                        'vagas_ocupadas': int(row.get('VAGAS_OCUPADAS', 0)) if pd.notna(row.get('VAGAS_OCUPADAS')) else 0,
                        'mes_ano': mes_ano
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Turma: {e}")
            
            print(f"   ✅ Turmas migradas: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR OCUPAÇÃO ====================
        if 'OCUPAÇÃO' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='OCUPAÇÃO')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    data_val = row.get('DATA')
                    if pd.notna(data_val):
                        data_val = pd.to_datetime(data_val).date()
                    else:
                        continue
                    
                    client.table('ocupacao').upsert({
                        'data': data_val,
                        'ambiente': str(row.get('AMBIENTE', '')),
                        'percentual_ocupacao': float(row.get('PERCENTUAL_OCUPACAO', 0)) if pd.notna(row.get('PERCENTUAL_OCUPACAO')) else 0,
                        'turno': str(row.get('TURNO', '')),
                        'mes_ano': mes_ano
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Ocupação: {e}")
            
            print(f"   ✅ Ocupação migrada: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR NÃO REGÊNCIA ====================
        if 'NÃO_REGÊNCIA' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='NÃO_REGÊNCIA')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    data_inicio = row.get('DATA_INICIO')
                    data_fim = row.get('DATA_FIM')
                    
                    if pd.notna(data_inicio):
                        data_inicio = pd.to_datetime(data_inicio).date()
                    else:
                        data_inicio = None
                    
                    if pd.notna(data_fim):
                        data_fim = pd.to_datetime(data_fim).date()
                    else:
                        data_fim = None
                    
                    client.table('nao_regencia').upsert({
                        'id_instrutor': str(row.get('ID_INSTRUTOR', '')),
                        'instrutor': str(row.get('INSTRUTOR', '')),
                        'data_inicio': data_inicio,
                        'data_fim': data_fim,
                        'horas_nao_regencia': float(row.get('HORAS_NAO_REGENCIA', 0)) if pd.notna(row.get('HORAS_NAO_REGENCIA')) else 0,
                        'tipo_atividade': str(row.get('TIPO_ATIVIDADE', '')),
                        'mes_ano': mes_ano
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Não Regência: {e}")
            
            print(f"   ✅ Não Regência migrada: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR DISCIPLINAS ====================
        if 'DISCIPLINAS' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='DISCIPLINAS')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    client.table('disciplinas').upsert({
                        'id_turma': str(row.get('ID_TURMA', '')),
                        'nome_disciplina': str(row.get('NOME_DISCIPLINA', '')),
                        'carga_horaria': float(row.get('CARGA_HORARIA', 0)) if pd.notna(row.get('CARGA_HORARIA')) else 0,
                        'status': str(row.get('STATUS', 'NÃO INICIADO')),
                        'mes_ano': mes_ano
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Disciplina: {e}")
            
            print(f"   ✅ Disciplinas migradas: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR FALTAS ====================
        if 'FALTAS' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='FALTAS')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    data_falta = row.get('DATA_FALTA')
                    if pd.notna(data_falta):
                        data_falta = pd.to_datetime(data_falta).date()
                    else:
                        continue
                    
                    client.table('faltas').upsert({
                        'data_falta': data_falta,
                        'instrutor': str(row.get('INSTRUTOR', '')),
                        'motivo': str(row.get('MOTIVO', '')),
                        'mes_ano': mes_ano
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Falta: {e}")
            
            print(f"   ✅ Faltas migradas: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR CALENDÁRIO ====================
        if 'CALENDÁRIO' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='CALENDÁRIO')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    data_val = row.get('DATA')
                    if pd.notna(data_val):
                        data_val = pd.to_datetime(data_val).date()
                    else:
                        continue
                    
                    client.table('calendario').upsert({
                        'data': data_val,
                        'tipo_dia': str(row.get('TIPO_DIA', 'Evento')),
                        'descricao': str(row.get('DESCRICAO', '')),
                        'mes_ano': mes_ano
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Calendário: {e}")
            
            print(f"   ✅ Calendário migrado: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR INSTRUTORES ====================
        if 'INSTRUTORES' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='INSTRUTORES')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    client.table('instrutores').upsert({
                        'id_instrutor': str(row.get('ID', '')),
                        'nome_completo': str(row.get('NOME_COMPLETO', ''))
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Instrutor: {e}")
            
            print(f"   ✅ Instrutores migrados: {registros}")
            total_registros += registros
        
        # ==================== MIGRAR AMBIENTES ====================
        if 'AMBIENTES' in abas_disponiveis:
            df = pd.read_excel(xl, sheet_name='AMBIENTES')
            registros = 0
            
            for _, row in df.iterrows():
                try:
                    client.table('ambientes').upsert({
                        'nome_ambiente': str(row.get('NOME_AMBIENTE', '')),
                        'tipo': str(row.get('TIPO', '')),
                        'virtual': bool(row.get('VIRTUAL', False)) if pd.notna(row.get('VIRTUAL')) else False
                    }).execute()
                    registros += 1
                except Exception as e:
                    resultado['erros'].append(f"Ambiente: {e}")
            
            print(f"   ✅ Ambientes migrados: {registros}")
            total_registros += registros
        
        xl.close()
        
        # Registrar auditoria
        if total_registros > 0:
            try:
                client.table('auditoria_upload').insert({
                    'usuario': 'migrate_script',
                    'nome_arquivo': arquivo_path.name,
                    'mes_ano': mes_ano,
                    'registros_inseridos': total_registros,
                    'status': 'SUCESSO' if not resultado['erros'] else 'PARCIAL'
                }).execute()
            except Exception:
                pass
        
        resultado['sucesso'] = total_registros > 0
        resultado['registros'] = total_registros
        resultado['mes_ano'] = mes_ano
        
        return resultado
    
    except Exception as e:
        erro_msg = f"Erro crítico: {e}"
        print(f"   ❌ {erro_msg}")
        resultado['erros'].append(erro_msg)
        xl.close() if 'xl' in locals() else None
        return resultado


def main():
    """Função principal de migração"""
    print("=" * 60)
    print("🚀 MIGRAÇÃO DE DADOS HISTÓRICOS - DIGITECH")
    print("=" * 60)
    
    # Verificar pasta histórico
    if not HISTORICO_DIR.exists():
        print(f"❌ Pasta {HISTORICO_DIR} não encontrada!")
        print("Crie a pasta e coloque os arquivos .xlsx nela.")
        sys.exit(1)
    
    # Listar arquivos
    arquivos_xlsx = list(HISTORICO_DIR.glob('*.xlsx'))
    
    if not arquivos_xlsx:
        print(f"❌ Nenhum arquivo .xlsx encontrado em {HISTORICO_DIR}")
        sys.exit(1)
    
    print(f"📁 {len(arquivos_xlsx)} arquivo(s) encontrado(s)")
    
    # Conectar ao Supabase
    client = conectar_supabase()
    
    if not client:
        print("\n💡 DICA: Execute este comando para instalar dependências:")
        print("   pip install supabase python-dotenv")
        sys.exit(1)
    
    # Migrar cada arquivo
    resultados = []
    
    for arquivo in sorted(arquivos_xlsx):
        resultado = migrar_arquivo(client, arquivo)
        resultados.append(resultado)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DA MIGRAÇÃO")
    print("=" * 60)
    
    sucessos = sum(1 for r in resultados if r['sucesso'])
    falhas = len(resultados) - sucessos
    total_registros = sum(r['registros'] for r in resultados)
    
    print(f"✅ Sucessos: {sucessos}/{len(resultados)}")
    print(f"❌ Falhas: {falhas}")
    print(f"📈 Total de registros migrados: {total_registros}")
    
    if falhas > 0:
        print("\n⚠️ Arquivos com problemas:")
        for r in resultados:
            if not r['sucesso'] and r['erros']:
                print(f"   - {r['arquivo']}: {r['erros'][0]}")
    
    print("\n✨ Migração concluída!")
    print("Agora você pode acessar o dashboard no Streamlit.")


if __name__ == '__main__':
    main()
