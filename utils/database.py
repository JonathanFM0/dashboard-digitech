"""
Módulo de conexão com o Supabase (PostgreSQL)
Arquitetura Híbrida: Prioriza banco de dados, fallback para arquivos locais
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
import streamlit as st

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class DatabaseConnection:
    """Gerencia conexão com Supabase e operações CRUD"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.connected = False
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Inicializa conexão usando secrets do Streamlit"""
        if not SUPABASE_AVAILABLE:
            st.warning("Biblioteca supabase não instalada. Usando modo offline.")
            return
        
        try:
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                self.client = create_client(supabase_url, supabase_key)
                self.connected = True
                st.success("✅ Conectado ao Supabase")
            else:
                st.info("📁 Credenciais do Supabase não configuradas. Usando arquivos locais.")
        except Exception as e:
            st.error(f"Erro ao conectar no Supabase: {str(e)}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Verifica se está conectado ao banco"""
        return self.connected and self.client is not None
    
    # ==================== LEITURA DE DADOS ====================
    
    def get_turmas(self, mes_ano: Optional[str] = None) -> pd.DataFrame:
        """Obtém dados de turmas"""
        if not self.connected:
            return self._fallback_read_excel('TURMAS')
        
        try:
            query = self.client.table('turmas').select('*')
            if mes_ano:
                query = query.eq('mes_ano', mes_ano)
            
            response = query.execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at', 'updated_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler turmas do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('TURMAS')
    
    def get_ocupacao(self, mes_ano: Optional[str] = None) -> pd.DataFrame:
        """Obtém dados de ocupação"""
        if not self.connected:
            return self._fallback_read_excel('OCUPAÇÃO')
        
        try:
            query = self.client.table('ocupacao').select('*')
            if mes_ano:
                query = query.eq('mes_ano', mes_ano)
            
            response = query.execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler ocupação do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('OCUPAÇÃO')
    
    def get_nao_regencia(self, mes_ano: Optional[str] = None) -> pd.DataFrame:
        """Obtém dados de não regência"""
        if not self.connected:
            return self._fallback_read_excel('NÃO_REGÊNCIA')
        
        try:
            query = self.client.table('nao_regencia').select('*')
            if mes_ano:
                query = query.eq('mes_ano', mes_ano)
            
            response = query.execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler não regência do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('NÃO_REGÊNCIA')
    
    def get_disciplinas(self, mes_ano: Optional[str] = None) -> pd.DataFrame:
        """Obtém dados de disciplinas"""
        if not self.connected:
            return self._fallback_read_excel('DISCIPLINAS')
        
        try:
            query = self.client.table('disciplinas').select('*')
            if mes_ano:
                query = query.eq('mes_ano', mes_ano)
            
            response = query.execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler disciplinas do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('DISCIPLINAS')
    
    def get_faltas(self, mes_ano: Optional[str] = None) -> pd.DataFrame:
        """Obtém dados de faltas"""
        if not self.connected:
            return self._fallback_read_excel('FALTAS')
        
        try:
            query = self.client.table('faltas').select('*')
            if mes_ano:
                query = query.eq('mes_ano', mes_ano)
            
            response = query.execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler faltas do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('FALTAS')
    
    def get_calendario(self, mes_ano: Optional[str] = None) -> pd.DataFrame:
        """Obtém dados do calendário"""
        if not self.connected:
            return self._fallback_read_excel('CALENDÁRIO')
        
        try:
            query = self.client.table('calendario').select('*')
            if mes_ano:
                query = query.eq('mes_ano', mes_ano)
            
            response = query.execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler calendário do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('CALENDÁRIO')
    
    def get_instrutores(self) -> pd.DataFrame:
        """Obtém dados de instrutores"""
        if not self.connected:
            return self._fallback_read_excel('INSTRUTORES')
        
        try:
            response = self.client.table('instrutores').select('*').execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler instrutores do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('INSTRUTORES')
    
    def get_ambientes(self) -> pd.DataFrame:
        """Obtém dados de ambientes"""
        if not self.connected:
            return self._fallback_read_excel('AMBIENTES')
        
        try:
            response = self.client.table('ambientes').select('*').execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler ambientes do DB: {e}. Usando fallback.")
        
        return self._fallback_read_excel('AMBIENTES')
    
    def get_parametros(self) -> Dict[str, Any]:
        """Obtém todos os parâmetros como dicionário"""
        if not self.connected:
            return {}
        
        try:
            response = self.client.table('parametros').select('*').execute()
            if response.data:
                return {row['parametro']: row['valor'] for row in response.data}
        except Exception as e:
            st.warning(f"Falha ao ler parâmetros do DB: {e}")
        
        return {}
    
    def get_metas_ha(self, mes_ano: str) -> pd.DataFrame:
        """Obtém metas manuais de Hora-Aluno"""
        if not self.connected:
            return pd.DataFrame()
        
        try:
            response = self.client.table('metas_ha').select('*').eq('mes_ano', mes_ano).execute()
            if response.data:
                df = pd.DataFrame(response.data)
                return df.drop(columns=['id', 'created_at', 'updated_at'], errors='ignore')
        except Exception as e:
            st.warning(f"Falha ao ler metas HA do DB: {e}")
        
        return pd.DataFrame()
    
    def get_all_meses_anos(self) -> List[str]:
        """Obtém lista única de meses/anos disponíveis"""
        if self.connected:
            try:
                response = self.client.table('ocupacao').select('mes_ano').execute()
                if response.data:
                    meses = sorted(list(set([row['mes_ano'] for row in response.data])))
                    if meses:
                        return meses
            except Exception:
                pass
        
        # Fallback: ler da pasta local
        return self._fallback_get_meses()
    
    def _fallback_get_meses(self) -> List[str]:
        """Obtém meses da pasta local como fallback"""
        import os
        from pathlib import Path
        
        historico_dir = Path('historico_dados')
        if not historico_dir.exists():
            return []
        
        meses = []
        for file in historico_dir.glob('*.xlsx'):
            try:
                xl = pd.ExcelFile(file)
                if 'OCUPAÇÃO' in xl.sheet_names:
                    df = pd.read_excel(xl, sheet_name='OCUPAÇÃO')
                    if 'DATA' in df.columns:
                        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
                        mes_ano = df['DATA'].dt.strftime('%Y-%m').dropna().unique()
                        meses.extend(mes_ano)
                xl.close()
            except Exception:
                continue
        
        return sorted(list(set(meses)))
    
    # ==================== ESCRITA DE DADOS ====================
    
    def insert_upload_auditoria(self, usuario: str, nome_arquivo: str, 
                                 mes_ano: str, registros: int, 
                                 status: str = 'SUCESSO', erro: str = None):
        """Registra auditoria de upload"""
        if not self.connected:
            return
        
        try:
            self.client.table('auditoria_upload').insert({
                'usuario': usuario,
                'nome_arquivo': nome_arquivo,
                'mes_ano': mes_ano,
                'registros_inseridos': registros,
                'status': status,
                'erro_mensagem': erro
            }).execute()
        except Exception as e:
            st.warning(f"Falha ao registrar auditoria: {e}")
    
    def upsert_turmas(self, df: pd.DataFrame, mes_ano: str):
        """Insere ou atualiza turmas"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                record['mes_ano'] = mes_ano
                self.client.table('turmas').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir turmas: {e}")
            return 0
    
    def upsert_ocupacao(self, df: pd.DataFrame, mes_ano: str):
        """Insere ou atualiza ocupação"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                record['mes_ano'] = mes_ano
                self.client.table('ocupacao').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir ocupação: {e}")
            return 0
    
    def upsert_nao_regencia(self, df: pd.DataFrame, mes_ano: str):
        """Insere ou atualiza não regência"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                record['mes_ano'] = mes_ano
                self.client.table('nao_regencia').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir não regência: {e}")
            return 0
    
    def upsert_disciplinas(self, df: pd.DataFrame, mes_ano: str):
        """Insere ou atualiza disciplinas"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                record['mes_ano'] = mes_ano
                self.client.table('disciplinas').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir disciplinas: {e}")
            return 0
    
    def upsert_faltas(self, df: pd.DataFrame, mes_ano: str):
        """Insere ou atualiza faltas"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                record['mes_ano'] = mes_ano
                self.client.table('faltas').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir faltas: {e}")
            return 0
    
    def upsert_calendario(self, df: pd.DataFrame, mes_ano: str):
        """Insere ou atualiza calendário"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                record['mes_ano'] = mes_ano
                self.client.table('calendario').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir calendário: {e}")
            return 0
    
    def upsert_instrutores(self, df: pd.DataFrame):
        """Insere ou atualiza instrutores"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                self.client.table('instrutores').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir instrutores: {e}")
            return 0
    
    def upsert_ambientes(self, df: pd.DataFrame):
        """Insere ou atualiza ambientes"""
        if not self.connected or df.empty:
            return 0
        
        try:
            records = df.to_dict('records')
            for record in records:
                self.client.table('ambientes').upsert(record).execute()
            return len(records)
        except Exception as e:
            st.error(f"Erro ao inserir ambientes: {e}")
            return 0
    
    def update_meta_ha(self, turma_id: Optional[str], meta_manual: float, mes_ano: str):
        """Atualiza ou cria meta manual de HA"""
        if not self.connected:
            return False
        
        try:
            self.client.table('metas_ha').upsert({
                'turma_id': turma_id,
                'meta_manual': meta_manual,
                'mes_ano': mes_ano
            }).execute()
            return True
        except Exception as e:
            st.error(f"Erro ao atualizar meta HA: {e}")
            return False
    
    # ==================== FALLBACK PARA ARQUIVOS ====================
    
    def _fallback_read_excel(self, aba_nome: str) -> pd.DataFrame:
        """Lê dados de arquivo Excel local como fallback"""
        # Implementação simplificada - será complementada pelo app.py
        return pd.DataFrame()


# Singleton para reutilizar conexão
@st.cache_resource
def get_db_connection() -> DatabaseConnection:
    """Obtém instância singleton da conexão com banco"""
    return DatabaseConnection()
